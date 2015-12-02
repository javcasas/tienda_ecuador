from datetime import datetime, date, timedelta
from decimal import Decimal
import pytz
import json
import xml.etree.ElementTree as ET

from django.test import TestCase, Client
from django.core.urlresolvers import reverse

from billing import models
import company_accounts.models

from helpers import (add_User,
                     TestHelpersMixin,
                     add_instance,
                     make_post)

from util.sri_models import SRIStatus, AmbienteSRI
from util.testsuite.test_sri_sender_mock import (
    MockAutorizarComprobante,
    MockEnviarComprobante,
    gen_respuesta_solicitud_ok,
    gen_respuesta_solicitud_invalid_xml,
    gen_respuesta_autorizacion_comprobante_valido)


def get_date():
    now = datetime.now(tz=pytz.timezone('America/Guayaquil'))
    return now.replace(microsecond=0)


def fix_keys(keys):
    bad_keys = ['date']
    return [k for k in keys if k not in bad_keys]


class NotLoggedInTests(TestCase):
    """
    Ensure no useful information can be get without logging in
    """
    def test_index(self):
        response = self.client.get(reverse('billing_index'))
        self.assertEqual(response.status_code, 302)

    def test_company_index(self):
        response = self.client.get(
            reverse('company_index', kwargs={'company_id': 1})
        )
        self.assertEqual(response.status_code, 302)


class LoggedInTests(TestCase, TestHelpersMixin):
    """
    Tests that support a logged-in user
    """
    def setUp(self):
        username, password = 'paco', 'paco_pw'
        self.user = add_User(username=username, password=password)
        self.c = Client()
        r = self.c.post("/accounts/login/",
                        {'username': username, 'password': password})
        # FIXME
        # self.assertRedirects(r, reverse('company_accounts:company_index'))

    def tearDown(self):
        self.assert_no_broken_urls()
        super(LoggedInTests, self).tearDown()

    def assertContainsObject(self, response, item, fields, msg=None):
        """
        Checks all the fields in a general object
        """
        for field in fields:
            value = getattr(item, field)
            self.assertContains(
                response, str(value), html=False,
                msg_prefix='Field {} ({}) not found'.format(field, value))

    def simulate_post(self, url, data_to_post, client=None, form_index=0):
        """
        Simulates a post
            Only commits data that is not in hidden fields
        """
        client = client or self.c
        source_html = client.get(url).content
        try:
            root = ET.fromstring(source_html)
        except ET.ParseError:
            open("test.xml", "w").write(source_html)
            raise
        data_to_post = make_post(data_to_post)
        data_to_use = {}

        current_form = root.findall(".//form")[form_index]
        # input fields, including hidden inputs
        for i in current_form.findall(".//input"):
            key = i.get('name')
            pre_value = i.get('value')
            type_ = i.get('type')
            # Pre-filled in values
            data_to_use[key] = pre_value or ""
            # Added values
            if type_ != "hidden" and data_to_post.get(key):
                data_to_use[key] = data_to_post.pop(key)
            if type_ == 'hidden' and data_to_post.get(key):
                self.fail(
                    "Test error: Attempt to post custom"
                    " value for hidden field: {} = {}".format(
                        key, data_to_post[key]))

        # textarea fields
        textareas = current_form.findall(".//textarea")
        for ta in textareas:
            key = ta.get('name')
            data_to_use[key] = data_to_post.pop(key, ta.text)

        # select fields
        selects = current_form.findall(".//select")
        for s in selects:
            key = s.get('name')
            selected_option = root.findall(
                ".//form//select[@name='{}']"
                "/option[@selected]".format(key))
            default = selected_option[0].get("value") if selected_option else ""
            data_to_use[key] = data_to_post.pop(key, default)

        # submit buttons
        buttons = current_form.findall(".//button")
        for bt in buttons:
            key = bt.get('name')
            value = bt.get('value')
            if str(data_to_post.get(key)) == value:
                data_to_use[key] = data_to_post.pop(key)
                break

        self.assertFalse(data_to_post,
                         "Items left in data to post: {}".format(data_to_post))
        return client.post(url, data_to_use)

    def assert_no_broken_urls(self):
        for model in [models.Item, models.Customer, models.Bill]:
            obs = model.objects.all()
            for ob in obs:
                r = self.c.get(ob.get_absolute_url())
                self.assertIn(r.status_code, [200, 404, 405])


class LoggedInWithCompanyTests(LoggedInTests):
    """
    Logged in user that is associated with a company
    """
    def setUp(self):
        super(LoggedInWithCompanyTests, self).setUp()
        self.company = add_instance(
            models.Company,
            nombre_comercial='Tienda 1',
            ruc='1234567890',
            razon_social='Paco Pil',
            direccion_matriz="C del pepino")

        self.company_user = add_instance(
            company_accounts.models.CompanyUser,
            user=self.user,
            company=self.company)

        self.company2 = add_instance(
            models.Company,
            nombre_comercial='Tienda 2',
            ruc='1234567892',
            razon_social='Paca Pil',
            direccion_matriz="C del pepano")

        self.establecimiento = add_instance(
            company_accounts.models.Establecimiento,
            company=self.company,
            descripcion="Matriz",
            direccion='C del pepino',
            codigo="001")

        self.punto_emision = add_instance(
            company_accounts.models.PuntoEmision,
            establecimiento=self.establecimiento,
            descripcion="Caja de la matriz",
            codigo="001"
        )


class IndexViewTests(LoggedInWithCompanyTests):
    def test_view_index_multiple_companies(self):
        """
        A logged-in user can view the billing index,
        and the index shows the available companies
        """
        add_instance(company_accounts.models.CompanyUser,
                     user=self.user, company=self.company2)

        response = self.c.get(reverse('billing_index'))
        self.assertEquals(response.status_code, 200)

        for c in [self.company, self.company2]:
            self.assertIn(c, response.context['companies'])
            self.assertContains(response, c)

    def test_view_index_single_company(self):
        """
        A logged-in user is redirected if he has only a single company
        """
        response = self.c.get(reverse('billing_index'))
        self.assertRedirects(response,
                             reverse('company_index', args=(self.company.id,)))

    def test_view_company_index(self):
        r = self.c.get(reverse('company_index', args=(self.company.id,)))
        self.assertContains(r, self.company.razon_social)
        self.assertContains(r, self.company.nombre_comercial)

    def test_view_company_index_access_denied(self):
        """
        A logged-in user can't view the index for a company he has no access
        """
        response = self.c.get(
            reverse('company_index', args=(self.company2.id,))
        )
        self.assertEquals(response.status_code, 404)


class GenericObjectCRUDTest(object):
    """
    Generic CRUD test for an object type
    Class variables:
        entity = 'customer'   # Name of the view
        cls = models.Customer # Class
        data = {'name': 'Pepe'}  # Data for new testing object
        newdata = {'name': 'Wis'} # Data for updating object
    """
    def make_object(self):
        """
        Makes the testing instance of the object,
        and initialises some variables
        """
        self.index_view = "{}_index".format(self.entity)
        self.create_view = "{}_create".format(self.entity)
        self.detail_view = "{}_detail".format(self.entity)
        self.update_view = "{}_update".format(self.entity)
        self.delete_view = "{}_delete".format(self.entity)
        self.ob = self.cls(company=self.company, **self.data)
        self.ob.save()
        self.index_keys = self.data.keys()
        self.reverse_index_args = (self.company.id,)
        self.reverse_object_args = (self.ob.id,)
        self.urls_to_test = [
            reverse(self.index_view, args=self.reverse_index_args),
            reverse(self.detail_view, args=self.reverse_object_args),
            reverse(self.create_view, args=self.reverse_index_args),
            reverse(self.update_view, args=self.reverse_object_args),
            reverse(self.delete_view, args=self.reverse_object_args),
        ]
        self.fields_in_view = self.data.keys()

    def test_index(self):
        """
        Tests the index
        """
        r = self.c.get(
            reverse(self.index_view, args=self.reverse_index_args))
        self.assertContainsObject(r, self.ob, self.index_keys)

    def test_view(self):
        """
        Tests viewing the object
        The test passes if:
            The view shows the attributes of the object
        """
        r = self.c.get(
            reverse(self.detail_view, args=self.reverse_object_args))
        self.assertContainsObject(r, self.ob, self.fields_in_view)

    def test_create_show_form(self):
        """
        Tests the form being shown.
        The test passes if:
            * All the data fields are in the form
            * There is a back link
        """
        r = self.c.get(
            reverse(self.create_view, args=self.reverse_index_args),
        )
        # Fields
        for key in self.data.keys():
            self.assertContains(r, key)
        # Back link
        self.assertContains(
            r, reverse(self.index_view, args=self.reverse_index_args))

    def test_create(self):
        """
        Tests creating a new object with self.data
        The test passes if:
            The object is created with the specified data
            The client is redirected to the object view
        """
        with self.new_item(self.cls) as new:
            r = self.simulate_post(
                reverse(self.create_view, args=self.reverse_index_args),
                self.data,
            )
        self.assertRedirects(
            r, reverse(self.detail_view,
                       args=(new.id,)))
        self.assertObjectMatchesData(new, self.data)

    def test_create_crossed_company_denied(self):
        """
        Tests creating a new object using a crossed request
        that pretends to create a new object under a different company
        """
        with self.assertRaises(AssertionError):
            with self.new_item(self.cls):
                self.c.post(
                    reverse(self.create_view, args=(self.company2.id,)),
                    make_post(self.data),
                )

    def test_update_show_form(self):
        """
        Tests the form being shown.
        The test passes if:
            * All the data fields are in the form
            * The data fields contain the current values
            * There is a back link
        """
        r = self.c.get(
            reverse(self.update_view, args=self.reverse_object_args),
        )
        # Fields
        for key in self.data.keys():
            self.assertContains(r, key)
        # Field values
        self.assertContainsObject(r, self.ob, self.data.keys())
        # Back link
        self.assertContains(
            r, reverse(self.detail_view, args=self.reverse_object_args))

    def test_update(self):
        """
        Tests updating an object with self.newdata
        The test passes if:
            The object has the new data
            The client is redirected to the object view
        """
        r = self.simulate_post(
            reverse(self.update_view, args=self.reverse_object_args),
            self.newdata,
        )
        self.assertRedirects(
            r, reverse(self.detail_view, args=self.reverse_object_args))
        self.assertObjectMatchesData(
            self.cls.objects.get(id=self.ob.id), self.newdata)

    def test_delete(self):
        """
        Tests deleting the object
        The test passes if:
            The object is deleted
            The client is redirected to the object index
        """
        r = self.simulate_post(
            reverse(self.delete_view, args=self.reverse_object_args),
            {}
        )
        self.assertRedirects(
            r, reverse(self.index_view, args=self.reverse_index_args))
        with self.assertRaises(self.cls.DoesNotExist):
            self.cls.objects.get(id=self.ob.id)

    def test_not_logged_in_access_denied(self):
        """
        Tests that no url can be reached without authentication
        """
        # Test get
        for url in self.urls_to_test:
            r = Client().get(url)
            msg = "Url {} can be GETted without authentication".format(url)
            self.assertEqual(r.status_code, 302, msg)
            self.assertRedirects(r, "/accounts/login/?next={}".format(url))
        # Test post
        for url in self.urls_to_test:
            r = Client().post(url, self.newdata)
            msg = "Url {} can be POSTed without authentication".format(url)
            self.assertEqual(r.status_code, 302, msg)
            self.assertRedirects(r, "/accounts/login/?next={}".format(url))

    def test_different_user_access_denied(self):
        """
        Test that no URL can be reached
        unless a corresponding CompanyUser exists
        """
        username, password = 'wisa', 'wis_pwa'
        user = add_User(username=username, password=password)
        company3 = add_instance(
            models.Company,
            nombre_comercial='Tienda 3',
            ruc='1234567842',
            razon_social='Pace Pil',
            direccion_matriz="C del pepeno")

        add_instance(
            company_accounts.models.CompanyUser,
            user=user, company=company3)

        c = Client()
        r = c.post("/accounts/login/",
                   {'username': username, 'password': password})
        self.assertEquals(r['location'],
                          "http://testserver" + reverse('company_accounts:company_select'))
        # Test get
        for url in self.urls_to_test:
            r = c.get(url)
            msg = "Url {} can be GETted from a different user".format(url)
            self.assertEqual(r.status_code, 404, msg)
        # Test post
        for url in self.urls_to_test:
            r = c.post(url, {})
            msg = "Url {} can be POSTed from a different user".format(url)
            # Some posts fail with method not allowed
            self.assertIn(r.status_code, [404, 405], msg)

    def test_index_view_shows_only_available_objects(self):
        """
        Test that no URL can be reached
        unless a corresponding CompanyUser exists
        """
        username, password = 'wisa', 'wis_pwa'
        user = add_User(username=username, password=password)
        company3 = add_instance(
            models.Company,
            nombre_comercial='Tienda 3',
            ruc='1234567842',
            razon_social='Pace Pil',
            direccion_matriz="C del pepeno")

        add_instance(
            company_accounts.models.CompanyUser,
            user=user, company=company3)

        establecimiento3 = add_instance(
            company_accounts.models.Establecimiento,
            company=company3,
            descripcion="Matriz",
            direccion='C del pepano',
            codigo="001",
        )

        add_instance(models.PuntoEmision,
                     establecimiento=establecimiento3,
                     descripcion="Caja de la matriz",
                     codigo="001")

        ob3 = self.cls(company=company3, **self.data)
        ob3.save()

        c = Client()
        r = c.post("/accounts/login/",
                   {'username': username, 'password': password})
        self.assertEquals(r['location'],
                          "http://testserver" + reverse('company_accounts:company_select'))

        reverse_index_args = (company3.id,)
        r = c.get(
            reverse(self.index_view, args=reverse_index_args))
        context_object_name = r.context_data['view'].context_object_name
        self.assertEquals(
            # queryset objects are never equal
            # so I have to convert them to lists to compare properly
            list(r.context_data[context_object_name]),
            list(self.cls.objects.filter(company=company3)),
            "The list view shows objects from a different company")

        r = self.c.get(
            reverse(self.index_view, args=self.reverse_index_args))
        context_object_name = r.context_data['view'].context_object_name
        self.assertEquals(
            # queryset objects are never equal
            # so I have to convert them to lists to compare properly
            list(r.context_data[context_object_name]),
            list(self.cls.objects.filter(company=self.company)),
            "The list view shows objects from a different company")


class LoggedInWithCustomerTests(LoggedInWithCompanyTests,
                                GenericObjectCRUDTest):
    """
    Logged in user that is associated with a company
    Has company and customers
    """
    entity = 'customer'
    cls = models.Customer
    data = {'razon_social': 'Pepe',
            "tipo_identificacion": "cedula",
            "identificacion": "1713831152",
            "email": "a@b.com",
            "direccion": "blebla street"}
    newdata = {'razon_social': 'Wis',
               "tipo_identificacion": "ruc",
               "identificacion": "1713831152001",
               "email": "c@d.com",
               "direccion": "nana street"}

    def setUp(self):
        super(LoggedInWithCustomerTests, self).setUp()
        self.make_object()
        self.index_keys = ['razon_social', 'identificacion']


class LoggedInWithItemTests(LoggedInWithCompanyTests, GenericObjectCRUDTest):
    """
    Logged in user that is associated with a company
    Has company and items
    """
    entity = 'item'
    cls = models.Item
    data = {'sku': 'P1234',
            'name': 'Item 1',
            'unit_cost': 5,
            'unit_price': 6.5,
            'tipo': 'producto',
            'description': 'Item 1 description',
            'decimales_qty': 0}
    newdata = {'sku': 'P12345',
               'name': 'Item 2',
               'unit_cost': 3,
               'unit_price': 6,
               'tipo': 'servicio',
               'description': 'Item 2 description',
               'decimales_qty': 1}

    def setUp(self):
        super(LoggedInWithItemTests, self).setUp()
        self.iva = add_instance(
            models.Iva,
            descripcion="12%", codigo='12', porcentaje=12.0)
        self.ice = add_instance(models.Ice,
                                descripcion="Bebidas gaseosas",
                                codigo='3051', porcentaje=50.0)
        self.make_object()
        self.ob.tax_items.add(self.iva, self.ice)
        self.index_keys = ['sku', 'name']
        self.fields_in_view = ['sku', 'name', 'unit_price', 'description']

    def test_create(self):
        self.iva2 = add_instance(models.Iva,
                                 descripcion="0%", codigo='2', porcentaje=0.0)
        self.ice2 = add_instance(models.Ice,
                                 descripcion="Otro",
                                 codigo='3052', porcentaje=150.0)
        with self.new_item(self.cls) as new:
            r = self.simulate_post(
                reverse(self.create_view, args=self.reverse_index_args),
                dict(self.data, iva=self.iva2.id, ice=self.ice2.id),
            )
        self.assertRedirects(
            r, reverse(self.detail_view,
                       args=(new.id,)))
        self.assertObjectMatchesData(new, self.data)

    def test_update(self):
        """
        Tests updating an object with self.newdata
        The test passes if:
            The object has the new data
            The client is redirected to the object view
        """
        self.iva2 = add_instance(models.Iva,
                                 descripcion="0%", codigo='2', porcentaje=0.0)
        self.ice2 = add_instance(models.Ice,
                                 descripcion="Otro",
                                 codigo='3052', porcentaje=150.0)
        r = self.simulate_post(
            reverse(self.update_view, args=self.reverse_object_args),
            dict(self.newdata, iva=self.iva2.id, ice=self.ice2.id),
        )
        self.assertRedirects(
            r, reverse(self.detail_view, args=self.reverse_object_args))
        self.assertObjectMatchesData(
            self.cls.objects.get(id=self.ob.id), self.newdata)
        ob = self.cls.objects.get(id=self.ob.id)
        self.assertEquals(ob.iva, self.iva2)
        self.assertEquals(ob.ice, self.ice2)


class BillTests(LoggedInWithCompanyTests):
    """
    Logged in user that is associated with a company
    Has company and items
    """
    entity = 'proforma'
    cls = models.Bill

    def setUp(self):
        super(self.__class__, self).setUp()
        self.customer_data = {
            'razon_social': 'Pepe',
            "tipo_identificacion": "cedula",
            "identificacion": "1713831152",
            "email": "a@b.com",
            "direccion": "blebla street",
        }
        self.new_customer_data = {
            'razon_social': 'Wis',
            "tipo_identificacion": "ruc",
            "identificacion": "1713831152001",
            "email": "a@d.com",
            "direccion": "pupu street",
        }
        self.customer = add_instance(
            models.Customer,
            company=self.company,
            **self.customer_data)
        self.new_customer = add_instance(
            models.Customer,
            company=self.company,
            **self.new_customer_data)
        self.establecimiento = add_instance(
            company_accounts.models.Establecimiento,
            company=self.company,
            codigo='001')
        self.punto_emision = add_instance(
            company_accounts.models.PuntoEmision,
            establecimiento=self.establecimiento,
            codigo='001')

        self.bill = add_instance(
            models.Bill,
            issued_to=self.customer,
            punto_emision=self.punto_emision,
            date=get_date(),
            company=self.company)

        iva = add_instance(models.Iva,
                           descripcion="12%", codigo="2", porcentaje=12.0)
        ice = add_instance(models.Ice,
                           descripcion="Bebidas gaseosas",
                           codigo=1000, porcentaje=50)
        self.items = []
        for i in range(5):
            ob = add_instance(
                models.BillItem,
                sku="SKU00{}".format(i),
                name='Item {}'.format(i),
                description='Description of item {}'.format(i),
                qty=3 + i,
                unit_cost=5,
                unit_price=12,
                bill=self.bill)
            ob.tax_items.add(iva, ice)
            self.items.append(ob)

        self.forma_pago = add_instance(
            models.FormaPago,
            codigo='01',
            descripcion='efectivo')

        self.plazo_pago_inmediato = add_instance(
            models.PlazoPago,
            unidad_tiempo='dias',
            tiempo=0,
            descripcion='Inmediato')

        self.plazo_pago_mes = add_instance(
            models.PlazoPago,
            unidad_tiempo='dias',
            tiempo=30,
            descripcion='30 dias')

    def test_proformabill_company_index(self):
        """
        Check the proforma bill company index view
        """
        r = self.c.get(reverse('bill_company_index',
                               args=(self.company.id,)))
        self.assertContainsObject(
            r, self.bill, ['number', 'issued_to'])
        self.assertEquals(
            list(r.context['bill_list']),
            [self.bill])
        # Edit link
        self.assertContains(
            r, reverse('bill_detail',
                       args=(self.bill.id,)))

    def test_proformabill_establecimiento_index(self):
        """
        Check the proforma bill index view
        """
        establecimiento2 = add_instance(
            company_accounts.models.Establecimiento,
            company=self.company,
            codigo='002')
        punto_emision2 = add_instance(
            models.PuntoEmision,
            establecimiento=establecimiento2,
            codigo='002')
        bill2 = add_instance(
            models.Bill,
            issued_to=self.customer,
            punto_emision=punto_emision2,
            date=get_date())
        r = self.c.get(reverse('bill_establecimiento_index',
                               args=(establecimiento2.id,)))
        self.assertContainsObject(
            r, self.bill, ['number', 'issued_to'])
        self.assertEquals(
            list(r.context['bill_list']),
            [bill2])
        # Edit link
        self.assertContains(
            r, reverse('bill_detail',
                       args=(bill2.id,)))

    def test_bill_punto_emision_index(self):
        """
        Check the proforma bill index view
        """
        punto_emision2 = add_instance(models.PuntoEmision,
                                      establecimiento=self.establecimiento,
                                      codigo='002')
        bill2 = add_instance(
            models.Bill,
            issued_to=self.customer,
            punto_emision=punto_emision2,
            date=get_date())

        r = self.c.get(reverse('bill_punto_emision_index',
                       args=(punto_emision2.id,)))
        self.assertContainsObject(
            r, bill2, ['number', 'issued_to'])
        self.assertEquals(
            list(r.context['bill_list']),
            [bill2])
        # Edit link
        self.assertContains(
            r, reverse('bill_detail',
                       args=(bill2.id,)))

    def test_bill_detail(self):
        """
        Check the proforma bill detail view
        """
        r = self.c.get(
            reverse('bill_detail',
                    args=(self.bill.id,)))

        for item in self.items:
            self.assertContainsObject(r, item, ['sku', 'name', 'qty'])
            self.assertContains(
                r,
                reverse(
                    'billitem_update',
                    args=(item.id,)))
            self.assertContains(
                r,
                reverse(
                    'billitem_delete',
                    args=(item.id,)))
        subtotal = sum([i.total_sin_impuestos + i.valor_ice
                        for i in self.items])
        self.assertContains(r, subtotal)          # Total sin IVA
        self.assertContains(r, subtotal * 12 / 100)   # IVA
        self.assertContains(r, subtotal * 112 / 100)   # Total con IVA

    def test_bill_create(self):
        """
        Check the proforma bill creation view
        """
        with self.new_item(self.cls) as new:
            r = self.c.get(reverse('bill_create',
                                   args=(self.punto_emision.id,)))
        self.assertRedirects(
            r, reverse('bill_detail', args=(new.id,)))

    def test_bill_update_show_form(self):
        """
        Check the proforma bill update view
        """
        r = self.c.get(
            reverse('bill_update',
                    args=(self.bill.id,)))
        self.assertContainsObject(r, self.customer,
                                  ['razon_social', 'identificacion'])

    def test_bill_update_submit(self):
        """
        Check the proforma bill update view
        """
        r = self.simulate_post(
            reverse('bill_update',
                    args=(self.bill.id,)),
            dict(issued_to=self.new_customer.id),
            form_index=1)
        self.assertRedirects(
            r, reverse('bill_detail',
                       args=(self.bill.id,)))

    def test_bill_delete_show_form(self):
        """
        Tests deleting the object
        The test passes if:
            The delete form is shown
        """
        r = self.c.get(
            reverse("bill_delete",
                    args=(self.bill.id,)))
        self.assertContains(r, self.bill.number)
        self.assertContains(r, self.bill.issued_to.razon_social)

    def test_bill_delete_submit(self):
        """
        Tests deleting the object
        The test passes if:
            The object is deleted
            The client is redirected to the object index
        """
        r = self.simulate_post(
            reverse("bill_delete",
                    args=(self.bill.id,)),
            {}
        )
        self.assertRedirects(
            r, reverse("bill_company_index", args=(self.company.id,)))
        with self.assertRaises(models.Bill.DoesNotExist):
            models.Bill.objects.get(id=self.bill.id)

    def test_bill_update_new_customer_show_form(self):
        """
        Check the proforma bill new customer view
        """
        r = self.c.get(
            reverse('bill_new_customer',
                    args=(self.bill.id,)))
        keys = ['razon_social', "tipo_identificacion", "identificacion",
                "email", "direccion"]
        for k in keys:
            self.assertContains(r, k)

    def test_bill_update_new_customer_submit(self):
        """
        Check the proforma bill update view
        """
        data = {'razon_social': 'Pepe a',
                "tipo_identificacion": "cedula",
                "identificacion": "1713831152",
                "email": "a@ba.com",
                "direccion": "blebla aaaa street"}
        with self.new_item(models.Customer) as new:
            r = self.simulate_post(
                reverse('bill_new_customer',
                        args=(self.bill.id,)),
                data)
        self.assertRedirects(
            r, reverse('bill_detail',
                       args=(self.bill.id,)))
        self.assertObjectMatchesData(new, data)
        self.assertObjectMatchesData(
            models.Bill.objects.get(id=self.bill.id).issued_to,
            data)

    def test_bill_immediate_payment_submit(self):
        """
        Check the proforma bill update view
        """
        r = self.simulate_post(
            reverse('bill_payment_details',
                    args=(self.bill.id,)),
            {'payment_method': self.forma_pago.id})
        self.assertRedirects(
            r, reverse('bill_detail',
                       args=(self.bill.id,)))

        self.assertEquals(len(self.bill.payment), 1)

        payment = self.bill.payment[0]
        self.assertEquals(payment.forma_pago, self.forma_pago)
        self.assertEquals(payment.plazo_pago, self.plazo_pago_inmediato)
        self.assertEquals(payment.porcentaje, 100)
        self.assertEquals(payment.bill, self.bill)

    def test_bill_deferred_payment_submit(self):
        """
        Check the proforma bill update view
        """
        r = self.simulate_post(
            reverse('bill_payment_details',
                    args=(self.bill.id,)),
            {'payment_method': self.forma_pago.id,
             'payment_time_to_pay': self.plazo_pago_mes.id},
            form_index=1)
        self.assertRedirects(
            r, reverse('bill_detail',
                       args=(self.bill.id,)))

        self.assertEquals(len(self.bill.payment), 1)

        payment = self.bill.payment[0]
        self.assertEquals(payment.forma_pago, self.forma_pago)
        self.assertEquals(payment.plazo_pago, self.plazo_pago_mes)
        self.assertEquals(payment.porcentaje, 100)
        self.assertEquals(payment.bill, self.bill)


class BillItemTests(LoggedInWithCompanyTests):
    """
    Logged in user that is associated with a company
    """
    def setUp(self):
        super(self.__class__, self).setUp()
        self.customer_data = {
            'razon_social': 'Pepe',
            "tipo_identificacion": "cedula",
            "identificacion": "1713831152",
            "email": "a@b.com",
            "direccion": "blebla street",
        }
        self.proformabill_data = {
            'number': '001-002-1234567890',
            'date': get_date(),
        }
        self.customer = add_instance(models.Customer,
                                     company=self.company,
                                     **self.customer_data)
        self.establecimiento = add_instance(company_accounts.models.Establecimiento,
                                            company=self.company,
                                            codigo='001')
        self.punto_emision = add_instance(models.PuntoEmision,
                                          establecimiento=self.establecimiento,
                                          codigo='001')
        self.bill = add_instance(
            models.Bill,
            issued_to=self.customer,
            punto_emision=self.punto_emision,
            company=self.company,
            **self.proformabill_data)
        self.iva = add_instance(
            models.Iva,
            descripcion="12%", porcentaje=12.0, codigo=2)
        self.ice = add_instance(
            models.Ice,
            descripcion="Bebidas gaseosas",
            codigo=3051, porcentaje=50.0)
        self.item_data = dict(
            sku='SKU222',
            name='Item 3',
            unit_cost=Decimal("5.3"),
            unit_price=8,
            decimales_qty=2,
            description='Item3 description')
        self.item = add_instance(
            models.Item,
            company=self.company,
            **self.item_data)
        self.item.tax_items.add(self.iva)
        self.proformabill_item_data = dict(
            sku="SKU001",
            name='Item 1',
            description='Description of item 1',
            unit_price=16,
            unit_cost=9.1,
            tipo='servicio',
            qty=3)
        self.bill_item = add_instance(
            models.BillItem,
            bill=self.bill,
            **self.proformabill_item_data)
        self.bill_item.tax_items.add(self.iva)

    def test_add_item_to_bill_show_form(self):
        r = self.c.get(
            reverse('bill_add_item',
                    args=(self.bill.id,)))
        self.assertContainsObject(r, self.item, ['sku', 'name'])

    def test_add_item_to_bill_submit(self):
        with self.new_item(models.BillItem) as new:
            self.simulate_post(
                reverse('bill_add_item',
                        args=(self.bill.id,)),
                {'copy_from': self.item.id,
                 'qty': 1})
        self.assertEquals(new.qty, 1)
        self.assertObjectMatchesData(new, self.item_data)

    def test_add_item_to_bill_repeated_submit(self):
        with self.new_item(models.BillItem) as new:
            self.simulate_post(
                reverse('bill_add_item',
                        args=(self.bill.id,)),
                {'copy_from': self.item.id,
                 'qty': 1})
        self.assertEquals(new.qty, 1)
        self.c.post(
            reverse('bill_add_item',
                    args=(self.bill.id,)),
            {'copy_from': self.item.id,
             'qty': 1})
        self.assertEquals(models.BillItem.objects.get(pk=new.pk).qty,
                          2)

    def test_edit_item_in_bill_form(self):
        r = self.c.get(
            reverse('billitem_update',
                    args=(self.bill_item.id,)))
        self.assertContainsObject(
            r,
            models.BillItem.objects.get(pk=self.bill_item.id),
            ['sku', 'name', 'description', 'qty'])

    def test_edit_item_in_bill_submit(self):
        new_qty = 9
        pk = self.bill_item.id
        self.simulate_post(
            reverse('billitem_update',
                    args=(pk,)),
            dict(qty=new_qty))
        self.assertEquals(
            models.BillItem.objects.get(id=pk).qty,
            new_qty)

    def test_delete_item_from_bill_submit(self):
        pk = self.bill_item.id
        self.simulate_post(
            reverse('billitem_delete',
                    args=(pk,)),
            {})
        with self.assertRaises(models.BillItem.DoesNotExist):
            models.BillItem.objects.get(pk=pk)

    def test_update_item_qty_js(self):
        r = self.c.post(
            reverse('billitem_update_js',
                    args=(self.bill_item.id,)),
            {'qty': 4})
        ob = models.BillItem.objects.get(id=self.bill_item.id)
        self.assertEquals(ob.qty, 4)
        self.assertEquals(r.content, 'Ok')


class EmitirFacturaTests(LoggedInWithCompanyTests):
    """
    Emision de factura
    """
    def setUp(self):
        super(self.__class__, self).setUp()
        self.customer_data = {
            'razon_social': 'Pepe',
            "tipo_identificacion": "cedula",
            "identificacion": "1713831152",
            "email": "a@b.com",
            "direccion": "blebla street",
        }
        self.proformabill_data = {
            'number': '001-002-1234567890',
            'date': datetime(2015, 7, 29, 14, 11, 0,
                             tzinfo=pytz.timezone('America/Guayaquil')),
        }
        self.customer = add_instance(models.Customer,
                                     company=self.company,
                                     **self.customer_data)
        self.establecimiento = add_instance(company_accounts.models.Establecimiento,
                                            company=self.company,
                                            codigo='023')
        self.punto_emision = add_instance(models.PuntoEmision,
                                          establecimiento=self.establecimiento,
                                          codigo='013',
                                          siguiente_secuencial_pruebas=10,
                                          siguiente_secuencial_produccion=14)
        self.bill = add_instance(
            models.Bill,
            punto_emision=self.punto_emision,
            issued_to=self.customer,
            **self.proformabill_data)
        self.iva = add_instance(
            models.Iva,
            descripcion="12%", porcentaje=12.0, codigo=2)
        self.ice = add_instance(
            models.Ice,
            descripcion="Bebidas gaseosas",
            codigo=3051, porcentaje=50.0)
        self.item_data = dict(
            sku='SKU222',
            name='Item 3',
            unit_cost=5.3,
            unit_price=8,
            description='Item3 description')
        self.item = add_instance(
            models.Item,
            company=self.company,
            **self.item_data)
        self.item.tax_items.add(self.iva)
        self.proformabill_item_data = dict(
            sku="SKU001",
            name='Item 1',
            description='Description of item 1',
            unit_cost=9.1,
            unit_price=16,
            qty=3)
        self.bill_item = add_instance(
            models.BillItem,
            bill=self.bill,
            **self.proformabill_item_data)
        self.bill_item.tax_items.add(self.iva, self.ice)

        def get_bill_from_db():
            return models.Bill.objects.get(id=self.bill.id)
        self.get_bill_from_db = get_bill_from_db

    def test_emitir_factura_prepare_to_send(self):
        """
        Prueba la aceptacion de la factura para ser enviada
        """
        self.company.licence.approve('professional', date(2020, 1, 1))
        r = self.c.get(
            reverse('bill_emit_accept',
                    args=(self.bill.id,)))
        self.assertContains(  # same link as POST
            r,
            reverse('bill_emit_accept',
                    args=(self.bill.id,)))
        # Ok, emitir
        r = self.c.post(
            reverse('bill_emit_accept',
                    args=(self.bill.id,)))

        bill = models.Bill.objects.get(id=self.bill.id)
        # La factura ha sido convertida a 'a enviar'
        self.assertEquals(bill.status, SRIStatus.options.ReadyToSend)
        self.assertEquals(bill.punto_emision, self.punto_emision)
        # La fecha acaba de ser generada
        self.assertTrue(get_date() - bill.date < timedelta(seconds=3))

    def test_emitir_factura_send_to_sri_xml_generation(self):
        """
        Prueba la generacion del XML
        """
        self.company.licence.approve('professional', date(2020, 1, 1))
        # Ok, emitir
        self.c.post(
            reverse('bill_emit_accept',
                    args=(self.bill.id,)))

        # overwrite date to make it coincide
        bill = self.get_bill_from_db()
        bill.date = datetime(2015, 7, 29, 10, 1, 44,
                             tzinfo=pytz.timezone('America/Guayaquil'))
        bill.secret_save()

        response = gen_respuesta_solicitud_invalid_xml(
            self.get_bill_from_db().clave_acceso)
        with MockEnviarComprobante(response) as request:
            r = self.c.post(
                reverse('bill_emit_send_to_sri',
                        args=(self.bill.id,)))

        # Comprobar XML
        d2 = lambda v: "{:.2f}".format(v)
        d6 = lambda v: "{:.6f}".format(v)
        z9 = lambda v: "{:09}".format(v)

        bill = self.get_bill_from_db()
        to_test = {
            # Info Tributaria
            "./infoTributaria/ambiente": '1',  # pruebas
            "./infoTributaria/tipoEmision": '1',  # online
            "./infoTributaria/razonSocial": self.company.razon_social,
            "./infoTributaria/nombreComercial": self.company.nombre_comercial,
            "./infoTributaria/ruc": self.company.ruc,
            "./infoTributaria/claveAcceso": "".join([
                self.bill.date.strftime("%d%m%Y"),
                '01',
                self.company.ruc,
                '1',
                "023013",
                "{:09}".format(bill.secuencial),
                "34567890",
                "1",
                "0"]),
            "./infoTributaria/codDoc": "01",  # factura
            "./infoTributaria/estab": "023",
            "./infoTributaria/ptoEmi": "013",
            "./infoTributaria/secuencial":
                z9(bill.secuencial),
            "./infoTributaria/dirMatriz": self.company.direccion_matriz,

            # Info Factura
            "./infoFactura/fechaEmision":
                self.bill.date.strftime("%d/%m/%Y"),
            "./infoFactura/obligadoContabilidad":
                "SI" if self.company.obligado_contabilidad else "NO",
            "./infoFactura/tipoIdentificacionComprador":
                "05",
            "./infoFactura/razonSocialComprador":
                self.bill.issued_to.razon_social,
            "./infoFactura/identificacionComprador":
                self.bill.issued_to.identificacion,
            "./infoFactura/totalSinImpuestos":
                d2(self.bill.total_sin_impuestos),
            "./infoFactura/totalDescuento":
                "0.00",

            # Impuestos
            "./infoFactura/totalConImpuestos/totalImpuesto[1]/codigo": "2",
            "./infoFactura/totalConImpuestos/totalImpuesto[1]/codigoPorcentaje":
                self.bill.items[0].iva.codigo,
            "./infoFactura/totalConImpuestos/totalImpuesto[1]/descuentoAdicional": '0.00',
            "./infoFactura/totalConImpuestos/totalImpuesto[1]/baseImponible":
                d2(self.bill.items[0].base_imponible_iva),
            "./infoFactura/totalConImpuestos/totalImpuesto[1]/valor":
                d2(self.bill.items[0].valor_iva),
            "./infoFactura/totalConImpuestos/totalImpuesto[0]/codigo": "3",
            "./infoFactura/totalConImpuestos/totalImpuesto[0]/codigoPorcentaje":
                self.bill.items[0].ice.codigo,
            "./infoFactura/totalConImpuestos/totalImpuesto[0]/descuentoAdicional": '0.00',
            "./infoFactura/totalConImpuestos/totalImpuesto[0]/baseImponible":
                d2(self.bill.items[0].base_imponible_ice),
            "./infoFactura/totalConImpuestos/totalImpuesto[0]/valor":
                d2(self.bill.items[0].valor_ice),

            "./infoFactura/propina": "0.00",
            "./infoFactura/importeTotal":
                d2(self.bill.total_con_impuestos),
            "./infoFactura/moneda": "DOLAR",

            # Detalle
            "./detalles/detalle[0]/descripcion":
                self.bill.items[0].description,
            "./detalles/detalle[0]/cantidad":
                d6(self.bill.items[0].qty),
            "./detalles/detalle[0]/precioUnitario":
                d6(self.bill.items[0].unit_price),
            "./detalles/detalle[0]/descuento": "0.00",
            "./detalles/detalle[0]/precioTotalSinImpuesto":
                d2(self.bill.items[0].total_sin_impuestos),
            # IVA item 1
            "./detalles/detalle[0]/impuestos/impuesto[1]/codigo": "2",
            "./detalles/detalle[0]/impuestos/impuesto[1]/codigoPorcentaje":
                self.bill.items[0].iva.codigo,
            "./detalles/detalle[0]/impuestos/impuesto[1]/tarifa":
                d2(self.bill.items[0].iva.porcentaje),
            "./detalles/detalle[0]/impuestos/impuesto[1]/baseImponible":
                d2(self.bill.items[0].base_imponible_iva),
            "./detalles/detalle[0]/impuestos/impuesto[1]/valor":
                d2(self.bill.items[0].valor_iva),
            # ICE item 1
            "./detalles/detalle[0]/impuestos/impuesto[0]/codigo": "3",
            "./detalles/detalle[0]/impuestos/impuesto[0]/codigoPorcentaje":
                self.bill.items[0].ice.codigo,
            "./detalles/detalle[0]/impuestos/impuesto[0]/tarifa":
                d2(self.bill.items[0].ice.porcentaje),
            "./detalles/detalle[0]/impuestos/impuesto[0]/baseImponible":
                d2(self.bill.items[0].base_imponible_ice),
            "./detalles/detalle[0]/impuestos/impuesto[0]/valor":
                d2(self.bill.items[0].valor_ice),
        }

        tree = ET.fromstring(bill.xml_content)
        for k, v in to_test.iteritems():
            node = tree.find(k)
            self.assertNotEquals(node, None,
                                 "Node {} does not exist".format(k))
            differences = []
            msg = "Bad value for node {}: \n'{}' (should be \n'{}')".format(
                k, node.text, v)
            if "claveAcceso" in k:
                for i, (a, b) in enumerate(zip(node.text, v)):
                    if a != b:
                        differences.append(
                            "Difference at char {}: '{}' != '{}'".format(i, a, b))
                msg = msg + "\n" + "\n".join(differences)
            self.assertEquals(node.text, v, msg)

        self.assertIn("<ds:Signature", bill.xml_content)  # Ensure there is a signature on the file

    def test_emitir_factura_send_to_sri_invalid_xml(self):
        """
        Prueba el envio de facturas
        """
        self.company.licence.approve('professional', date(2020, 1, 1))
        # Ok, emitir
        self.c.post(
            reverse('bill_emit_accept',
                    args=(self.bill.id,)))

        with MockEnviarComprobante(gen_respuesta_solicitud_invalid_xml(self.get_bill_from_db().clave_acceso)) as request:
            r = self.c.post(
                reverse('bill_emit_send_to_sri',
                        args=(self.bill.id,)))

        bill = self.get_bill_from_db()
        self.assertEquals(request.request_args['xml_data'], bill.xml_content)
        self.assertEquals(request.request_args['entorno'], bill.ambiente_sri)

        self.assertEquals(r.status_code, 412)
        self.assertEquals(r.reason_phrase, "Precondition Failed")

        # Got an error, bill is 'not sent' again
        bill = self.get_bill_from_db()
        self.assertEquals(bill.status, SRIStatus.options.NotSent)
        self.assertTrue(bill.issues)  # There are issues
        issues = json.loads(bill.issues)
        for issue in issues:
            # The issues are really issues
            self.assertTrue(issues[0]['identificador'])
            self.assertTrue(issues[0]['mensaje'])
            self.assertTrue(issues[0]['tipo'])
        # There is at least an error
        self.assertTrue(any([issue['tipo'] == 'ERROR' for issue in issues]))

    def test_emitir_factura_send_to_sri_accepted(self):
        """
        Prueba el envio de facturas
        """
        self.company.licence.approve('professional', date(2020, 1, 1))
        # Ok, emitir
        self.c.post(
            reverse('bill_emit_accept',
                    args=(self.bill.id,)))

        prev_secuencial_pruebas = self.punto_emision.siguiente_secuencial_pruebas
        prev_secuencial_produccion = self.punto_emision.siguiente_secuencial_produccion

        with MockEnviarComprobante(gen_respuesta_solicitud_ok()) as request:
            r = self.c.post(
                reverse('bill_emit_send_to_sri',
                        args=(self.bill.id,)))

        bill = self.get_bill_from_db()
        self.assertEquals(request.request_args['xml_data'], bill.xml_content)
        self.assertEquals(request.request_args['entorno'], bill.ambiente_sri)

        self.assertEquals(r.status_code, 200)
        self.assertEquals(r.content, "Ok")

        # All OK
        bill = self.get_bill_from_db()
        self.assertEquals(bill.status, SRIStatus.options.Sent)
        self.assertFalse(bill.issues)  # There are no issues
        new_punto_emision = models.PuntoEmision.objects.get(id=self.punto_emision.id)

        # The counters are incremented
        self.assertEquals(prev_secuencial_pruebas + 1,
                          new_punto_emision.siguiente_secuencial_pruebas)
        self.assertEquals(prev_secuencial_produccion,
                          new_punto_emision.siguiente_secuencial_produccion)

    def test_emitir_factura_send_to_sri_accepted_produccion(self):
        """
        Prueba el envio de facturas
        """
        self.company.licence.approve('professional', date(2020, 1, 1))
        self.punto_emision.ambiente_sri = 'produccion'
        self.punto_emision.save()
        self.assertEquals(models.PuntoEmision.objects.get(id=self.punto_emision.id).ambiente_sri, 'produccion')
        # Ok, emitir
        self.c.post(
            reverse('bill_emit_accept',
                    args=(self.bill.id,)))

        prev_secuencial_pruebas = self.punto_emision.siguiente_secuencial_pruebas
        prev_secuencial_produccion = self.punto_emision.siguiente_secuencial_produccion

        with MockEnviarComprobante(gen_respuesta_solicitud_ok()) as request:
            r = self.c.post(
                reverse('bill_emit_send_to_sri',
                        args=(self.bill.id,)))

        bill = self.get_bill_from_db()
        self.assertEquals(request.request_args['xml_data'], bill.xml_content)
        self.assertEquals(request.request_args['entorno'], 'produccion')

        self.assertEquals(r.status_code, 200)
        self.assertEquals(r.content, "Ok")

        # All OK
        bill = self.get_bill_from_db()
        self.assertEquals(bill.status, SRIStatus.options.Sent)
        self.assertFalse(bill.issues)  # There are no issues
        self.assertEquals(bill.ambiente_sri, 'produccion')
        new_punto_emision = models.PuntoEmision.objects.get(id=self.punto_emision.id)

        # The counters are incremented
        self.assertEquals(prev_secuencial_produccion + 1,
                          new_punto_emision.siguiente_secuencial_produccion)
        self.assertEquals(prev_secuencial_pruebas,
                          new_punto_emision.siguiente_secuencial_pruebas)

    def test_emitir_factura_validation_accepted(self):
        """
        Prueba la validacion de una factura enviada
        """
        self.company.licence.approve('professional', date(2020, 1, 1))
        # Ok, emitir
        self.c.post(
            reverse('bill_emit_accept',
                    args=(self.bill.id,)))

        bill = self.get_bill_from_db()
        prev_secuencial_pruebas = self.punto_emision.siguiente_secuencial_pruebas
        prev_secuencial_produccion = self.punto_emision.siguiente_secuencial_produccion

        # Enviar factura
        with MockEnviarComprobante(gen_respuesta_solicitud_ok()) as request:
            r = self.c.post(
                reverse('bill_emit_send_to_sri',
                        args=(self.bill.id,)))

        bill = self.get_bill_from_db()
        self.assertEquals(request.request_args['xml_data'], bill.xml_content)
        self.assertEquals(request.request_args['entorno'], bill.ambiente_sri)

        # Factura aceptada
        response = gen_respuesta_autorizacion_comprobante_valido(self.bill.clave_acceso,
                                                                 self.bill.xml_content)
        with MockAutorizarComprobante(response) as request:
            r = self.c.post(
                reverse('bill_emit_validate',
                        args=(self.bill.id,)))

        self.assertEquals(request.request_args['clave_acceso'], bill.clave_acceso)
        self.assertEquals(request.request_args['entorno'], bill.ambiente_sri)

        self.assertEquals(r.status_code, 200)
        self.assertEquals(r.content, "Ok")

        # All OK
        bill = self.get_bill_from_db()
        self.assertEquals(bill.status, SRIStatus.options.Accepted)
        for issue in json.loads(bill.issues):
            self.assertFalse(issue)  # There are no issues


class PopulateBillingTest(TestCase):
    """
    Weird conditions detected with populate_billing
    """
    def test(self):
        import load_fixtures
        load_fixtures.stdout = lambda *args: None
        load_fixtures.main()
        import populate_billing
        populate_billing.print_instance = lambda a, b: None
        data = populate_billing.my_populate()

        c = Client()
        r = c.post("/accounts/login/",
                   {'username': 'javier', 'password': 'tiaputa'})
        self.assertEquals(r['location'],
                          "http://testserver" + reverse('company_accounts:company_select'))

        # It seems I can view customers and items for a different company
        # FIXME: re-enable tests
        urls = [
            # reverse("customer_detail", args=(data['c3'].id,)),
            # reverse("item_detail", args=(data['i22'].id,)),
            # reverse("bill_detail",
            #         args=(data['b3'].id,)),
        ]
        for url in urls:
            r = c.get(url)
            self.assertEquals(
                r.status_code, 404,
                "URL {} can be reached from a different user".format(url))
