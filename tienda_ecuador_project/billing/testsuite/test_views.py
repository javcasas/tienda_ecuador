from datetime import datetime
from decimal import Decimal
import base64
import pytz
import xml.etree.ElementTree as ET

from django.test import TestCase, Client
from django.core.urlresolvers import reverse

from billing import models

from helpers import (add_Company,
                     add_CompanyUser,
                     add_User, TestHelpersMixin,
                     add_instance,
                     make_post)


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
        response = self.client.get(reverse('index'))
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
        self.assertRedirects(r, reverse('index'))

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

    def simulate_post(self, url, data_to_post, client=None):
        """
        Simulates a post
            Only commits data that is not in hidden fields
        """
        client = client or self.c
        source_html = client.get(url).content
        try:
            root = ET.fromstring(source_html)
        except:
            open("test.xml", "w").write(source_html)
            raise
        data_to_post = make_post(data_to_post)
        data_to_use = {}

        # input fields, including hidden inputs
        inputs = root.findall(".//form//input")
        for i in inputs:
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
        textareas = root.findall(".//form//textarea")
        for ta in textareas:
            key = ta.get('name')
            data_to_use[key] = data_to_post.pop(key, ta.text)

        # select fields
        selects = root.findall(".//form//select")
        for s in selects:
            key = s.get('name')
            selected_option = root.findall(
                ".//form//select[@name='{}']"
                "/option[@selected]".format(key))
            default = selected_option[0].get("value") if selected_option else ""
            data_to_use[key] = data_to_post.pop(key, default)

        self.assertFalse(data_to_post, "Items left in data to post: {}".format(data_to_post))
        return client.post(url, data_to_use)

    def assert_no_broken_urls(self):
        for model in [models.Item, models.Customer, models.ProformaBill]:
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
        self.company = add_Company(
            nombre_comercial='Tienda 1',
            ruc='1234567890',
            razon_social='Paco Pil',
            direccion_matriz="C del pepino")
        self.company_user = add_CompanyUser(user=self.user,
                                            company=self.company)
        self.company2 = add_Company(
            nombre_comercial='Tienda 2',
            ruc='1234567892',
            razon_social='Paca Pil',
            direccion_matriz="C del pepano")

        self.establecimiento = add_instance(
            models.Establecimiento,
            company=self.company,
            descripcion="Matriz",
            direccion='C del pepino',
            codigo="001",
        )

        self.punto_emision = add_instance(
            models.PuntoEmision,
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
        add_CompanyUser(user=self.user, company=self.company2)

        response = self.c.get(reverse('index'))
        self.assertEquals(response.status_code, 200)

        for c in [self.company, self.company2]:
            self.assertIn(c, response.context['companies'])
            self.assertContains(response, c)

    def test_view_index_single_company(self):
        """
        A logged-in user is redirected if he has only a single company
        """
        response = self.c.get(reverse('index'))
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
        company3 = add_Company(
            nombre_comercial='Tienda 3',
            ruc='1234567842',
            razon_social='Pace Pil',
            direccion_matriz="C del pepeno")
        add_CompanyUser(user=user, company=company3)
        c = Client()
        r = c.post("/accounts/login/",
                   {'username': username, 'password': password})
        self.assertEquals(r['location'],
                          "http://testserver" + reverse('index'))
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
        company3 = add_Company(
            nombre_comercial='Tienda 3',
            ruc='1234567842',
            razon_social='Pace Pil',
            direccion_matriz="C del pepeno")
        add_CompanyUser(user=user, company=company3)
        establecimiento3 = add_instance(
            models.Establecimiento,
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
                          "http://testserver" + reverse('index'))

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
        self.iva = add_instance(models.Iva,
                                descripcion="12%", codigo='12', porcentaje=12.0)
        self.ice = add_instance(models.Ice,
                                descripcion="Bebidas gaseosas", grupo=1,
                                codigo='3051', porcentaje=50.0)
        self.make_object()
        self.ob.tax_items.add(self.iva, self.ice)
        self.index_keys = ['sku', 'name']
        self.fields_in_view = ['sku', 'name', 'unit_price', 'description']

    def test_create(self):
        self.iva2 = add_instance(models.Iva,
                                 descripcion="0%", codigo='2', porcentaje=0.0)
        self.ice2 = add_instance(models.Ice,
                                 descripcion="Otro", grupo=1,
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
                                 descripcion="Otro", grupo=1,
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


class ProformaBillTests(LoggedInWithCompanyTests):
    """
    Logged in user that is associated with a company
    Has company and items
    """
    entity = 'proforma'
    cls = models.ProformaBill

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
        self.data = {
            'number': '001-002-1234567890',
        }
        self.new_data = {
            'number': '002-004-0987654321',
        }
        self.customer = add_instance(models.Customer,
                                     company=self.company,
                                     **self.customer_data)
        self.new_customer = add_instance(models.Customer,
                                         company=self.company,
                                         **self.new_customer_data)
        self.establecimiento = add_instance(models.Establecimiento,
                                            company=self.company,
                                            codigo='001')
        self.punto_emision = add_instance(models.PuntoEmision,
                                          establecimiento=self.establecimiento,
                                          codigo='001')

        self.proformabill = add_instance(
            models.ProformaBill,
            issued_to=self.customer,
            punto_emision=self.punto_emision,
            date=get_date(),
            **self.data)

        iva = add_instance(models.Iva,
                           descripcion="12%", codigo="2", porcentaje=12.0)
        ice = add_instance(models.Ice,
                           descripcion="Bebidas gaseosas", grupo=1,
                           codigo=1000, porcentaje=50)
        self.items = []
        for i in range(5):
            ob = add_instance(
                models.ProformaBillItem,
                sku="SKU00{}".format(i),
                name='Item {}'.format(i),
                description='Description of item {}'.format(i),
                qty=3 + i,
                unit_cost=5,
                unit_price=12,
                proforma_bill=self.proformabill)
            ob.tax_items.add(iva, ice)
            self.items.append(ob)

    def test_proformabill_company_index(self):
        """
        Check the proforma bill company index view
        """
        r = self.c.get(reverse('proformabill_company_index',
                               args=(self.company.id,)))
        self.assertContainsObject(
            r, self.proformabill, ['number', 'issued_to'])
        self.assertEquals(
            list(r.context['proformabill_list']),
            [self.proformabill])
        # Edit link
        self.assertContains(
            r, reverse('proformabill_detail',
                       args=(self.proformabill.id,)))

    def test_proformabill_establecimiento_index(self):
        """
        Check the proforma bill index view
        """
        establecimiento2 = add_instance(models.Establecimiento,
                                        company=self.company,
                                        codigo='002')
        punto_emision2 = add_instance(models.PuntoEmision,
                                      establecimiento=establecimiento2,
                                      codigo='002')
        proformabill2 = add_instance(
            models.ProformaBill,
            issued_to=self.customer,
            punto_emision=punto_emision2,
            date=get_date(),
            **self.data)
        r = self.c.get(reverse('proformabill_establecimiento_index',
                               args=(establecimiento2.id,)))
        self.assertContainsObject(
            r, self.proformabill, ['number', 'issued_to'])
        self.assertEquals(
            list(r.context['proformabill_list']),
            [proformabill2])
        # Edit link
        self.assertContains(
            r, reverse('proformabill_detail',
                       args=(proformabill2.id,)))

    def test_proformabill_punto_emision_index(self):
        """
        Check the proforma bill index view
        """
        punto_emision2 = add_instance(models.PuntoEmision,
                                      establecimiento=self.establecimiento,
                                      codigo='002')
        proformabill2 = add_instance(
            models.ProformaBill,
            issued_to=self.customer,
            punto_emision=punto_emision2,
            date=get_date(),
            **self.data)

        r = self.c.get(reverse('proformabill_punto_emision_index',
                       args=(punto_emision2.id,)))
        self.assertContainsObject(
            r, proformabill2, ['number', 'issued_to'])
        self.assertEquals(
            list(r.context['proformabill_list']),
            [proformabill2])
        # Edit link
        self.assertContains(
            r, reverse('proformabill_detail',
                       args=(proformabill2.id,)))

    def test_proformabill_detail(self):
        """
        Check the proforma bill detail view
        """
        r = self.c.get(
            reverse('proformabill_detail',
                    args=(self.proformabill.id,)))
        self.assertContainsObject(r, self.proformabill,
                                  fix_keys(self.data.keys()))
        for item in self.items:
            self.assertContainsObject(r, item, ['sku', 'name', 'qty'])
            self.assertContains(
                r,
                reverse(
                    'proformabillitem_update',
                    args=(item.id,)))
            self.assertContains(
                r,
                reverse(
                    'proformabillitem_delete',
                    args=(item.id,)))
        subtotal = sum([i.total_sin_impuestos + i.valor_ice
                        for i in self.items])
        self.assertContains(r, subtotal)          # Total sin IVA
        self.assertContains(r, subtotal * 12 / 100)   # IVA
        self.assertContains(r, subtotal * 112 / 100)   # Total con IVA

    def test_proformabill_create_show_form(self):
        """
        Check the proforma bill creation view
        """
        r = self.c.get(reverse('proformabill_create',
                               args=(self.punto_emision.id,)))
        for field in ['number', 'issued_to']:
            self.assertContains(r, field)

    def test_proformabill_create_submit(self):
        """
        Check the proforma bill creation view
        """
        proformabill_data = {
            'number': '6666',
        }
        customer, created = models.Customer.objects.get_or_create(
            company=self.company,
            **self.customer_data)
        with self.new_item(self.cls) as new:
            r = self.simulate_post(
                reverse('proformabill_create', args=(self.punto_emision.id,)),
                dict(proformabill_data, issued_to=customer.id),
            )
        self.assertRedirects(
            r, reverse('proformabill_detail', args=(new.id,)))
        self.assertObjectMatchesData(new, proformabill_data)
        self.assertObjectMatchesData(new.issued_to, self.customer_data)

    def test_proformabill_update_show_form(self):
        """
        Check the proforma bill update view
        """
        r = self.c.get(
            reverse('proformabill_update',
                    args=(self.proformabill.id,)))
        self.assertContainsObject(r, self.customer,
                                  ['razon_social', 'identificacion'])
        self.assertContainsObject(r, self.proformabill,
                                  fix_keys(self.data.keys()))

    def test_proformabill_update_submit(self):
        """
        Check the proforma bill update view
        """
        r = self.simulate_post(
            reverse('proformabill_update',
                    args=(self.proformabill.id,)),
            dict(self.new_data, issued_to=self.new_customer.id))
        self.assertRedirects(
            r, reverse('proformabill_detail',
                       args=(self.proformabill.id,)))
        self.assertObjectMatchesData(
            models.ProformaBill.objects.get(id=self.proformabill.id),
            self.new_data)

    def test_proformabill_delete_show_form(self):
        """
        Tests deleting the object
        The test passes if:
            The delete form is shown
        """
        r = self.c.get(
            reverse("proformabill_delete",
                    args=(self.proformabill.id,)))
        self.assertContains(r, self.proformabill.number)
        self.assertContains(r, self.proformabill.issued_to.razon_social)

    def test_proformabill_delete_submit(self):
        """
        Tests deleting the object
        The test passes if:
            The object is deleted
            The client is redirected to the object index
        """
        r = self.simulate_post(
            reverse("proformabill_delete",
                    args=(self.proformabill.id,)),
            {}
        )
        self.assertRedirects(
            r, reverse("proformabill_company_index", args=(self.company.id,)))
        with self.assertRaises(models.ProformaBill.DoesNotExist):
            models.ProformaBill.objects.get(id=self.proformabill.id)


class ProformaBillItemTests(LoggedInWithCompanyTests):
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
        self.establecimiento = add_instance(models.Establecimiento,
                                            company=self.company,
                                            codigo='001')
        self.punto_emision = add_instance(models.PuntoEmision,
                                          establecimiento=self.establecimiento,
                                          codigo='001')
        self.proformabill = add_instance(
            models.ProformaBill,
            issued_to=self.customer,
            punto_emision=self.punto_emision,
            **self.proformabill_data)
        self.iva = add_instance(
            models.Iva,
            descripcion="12%", porcentaje=12.0, codigo=2)
        self.ice = add_instance(
            models.Ice,
            descripcion="Bebidas gaseosas", grupo=1,
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
            qty=3)
        self.proformabill_item = add_instance(
            models.ProformaBillItem,
            proforma_bill=self.proformabill,
            unit_cost=9.1,
            **self.proformabill_item_data)
        self.proformabill_item.tax_items.add(self.iva)

    def test_add_item_to_bill_show_form(self):
        r = self.c.get(
            reverse('proformabill_add_item',
                    args=(self.proformabill.id,)))
        self.assertContainsObject(r, self.item, ['sku', 'name'])

    def test_add_item_to_bill_submit(self):
        with self.new_item(models.ProformaBillItem) as new:
            self.simulate_post(
                reverse('proformabill_add_item',
                        args=(self.proformabill.id,)),
                {'copy_from': self.item.id,
                 'qty': 1})
        self.assertEquals(new.qty, 1)
        self.assertObjectMatchesData(new, self.item_data)

    def test_add_item_to_bill_repeated_submit(self):
        with self.new_item(models.ProformaBillItem) as new:
            self.simulate_post(
                reverse('proformabill_add_item',
                        args=(self.proformabill.id,)),
                {'copy_from': self.item.id,
                 'qty': 1})
        self.assertEquals(new.qty, 1)
        self.c.post(
            reverse('proformabill_add_item',
                    args=(self.proformabill.id,)),
            {'copy_from': self.item.id,
             'qty': 1})
        self.assertEquals(models.ProformaBillItem.objects.get(pk=new.pk).qty,
                          2)

    def test_edit_item_in_bill_form(self):
        r = self.c.get(
            reverse('proformabillitem_update',
                    args=(self.proformabill_item.id,)))
        self.assertContainsObject(
            r,
            models.ProformaBillItem.objects.get(pk=self.proformabill_item.id),
            ['sku', 'name', 'description', 'qty'])

    def test_edit_item_in_bill_submit(self):
        new_qty = 9
        pk = self.proformabill_item.id
        self.simulate_post(
            reverse('proformabillitem_update',
                    args=(pk,)),
            dict(qty=new_qty))
        self.assertEquals(
            models.ProformaBillItem.objects.get(id=pk).qty,
            new_qty)

    def test_delete_item_from_bill_submit(self):
        pk = self.proformabill_item.id
        self.simulate_post(
            reverse('proformabillitem_delete',
                    args=(pk,)),
            {})
        with self.assertRaises(models.ProformaBillItem.DoesNotExist):
            models.ProformaBillItem.objects.get(pk=pk)


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
        self.establecimiento = add_instance(models.Establecimiento,
                                            company=self.company,
                                            codigo='001')
        self.punto_emision = add_instance(models.PuntoEmision,
                                          establecimiento=self.establecimiento,
                                          codigo='001',
                                          siguiente_secuencial_pruebas=10,
                                          siguiente_secuencial_produccion=14)
        self.proformabill = add_instance(
            models.ProformaBill,
            punto_emision=self.punto_emision,
            issued_to=self.customer,
            **self.proformabill_data)
        self.iva = add_instance(
            models.Iva,
            descripcion="12%", porcentaje=12.0, codigo=2)
        self.ice = add_instance(
            models.Ice,
            descripcion="Bebidas gaseosas", grupo=1,
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
        self.proformabill_item = add_instance(
            models.ProformaBillItem,
            proforma_bill=self.proformabill,
            **self.proformabill_item_data)
        self.proformabill_item.tax_items.add(self.iva, self.ice)

    def test_emitir_factura(self):
        """
        Prueba la emision de facturas
        """
        self.company.cert = base64.b64encode(
            open("billing/testsuite/keystore.PKCS12").read())
        self.company.key = "123456"
        self.company.save()
        # Confirmar la emision de la factura
        r = self.c.get(
            reverse('proformabill_emit_to_bill',
                    args=(self.proformabill.id,)))
        self.assertContains(  # same link as POST
            r,
            reverse('proformabill_emit_to_bill',
                    args=(self.proformabill.id,)))
        # Ok, emitir
        r = self.c.post(
            reverse('proformabill_emit_to_bill',
                    args=(self.proformabill.id,)))

        # Generar XML
        #   Generar claves para el XML
        #       Guardar secuencial para el XML
        #       Incrementar secuencial de punto emision
        #   Firmar XML
        #   Guardar XML en proforma
        proforma = models.ProformaBill.objects.get(id=self.proformabill.id)
        self.assertEquals(
            proforma.secuencial_pruebas,
            10)
        self.assertEquals(
            models.PuntoEmision.objects.get(id=self.punto_emision.id).siguiente_secuencial_pruebas,
            11)
        r = self.c.get(
            reverse('proformabill_emit_gen_xml',
                    args=(self.proformabill.id,)))
        tree = ET.fromstring(r.content)

        d2 = lambda v: "{:.2f}".format(v)
        d6 = lambda v: "{:.6f}".format(v)
        z9 = lambda v: "{:09}".format(v)

        to_test = {
            # Info Tributaria
            "./infoTributaria/ambiente": '1',  # pruebas
            "./infoTributaria/tipoEmision": '1',  # online
            "./infoTributaria/razonSocial": self.company.razon_social,
            "./infoTributaria/nombreComercial": self.company.nombre_comercial,
            "./infoTributaria/ruc": self.company.ruc,
            "./infoTributaria/claveAcceso": "".join([
                self.proformabill.date.strftime("%d%m%Y"),
                '01',
                self.company.ruc,
                '1',
                "023013",
                "{:09}".format(proforma.secuencial_pruebas),
                "17907461",
                "1",
                "8"]),
            "./infoTributaria/codDoc": "01",  # factura
            "./infoTributaria/estab": "001",
            "./infoTributaria/ptoEmi": "001",
            "./infoTributaria/secuencial":
                z9(proforma.secuencial_pruebas),
            "./infoTributaria/dirMatriz": self.company.direccion_matriz,

            # Info Factura
            "./infoFactura/fechaEmision":
                self.proformabill.date.strftime("%d/%m/%Y"),
            "./infoFactura/obligadoContabilidad":
                "SI" if self.company.obligado_contabilidad else "NO",
            "./infoFactura/tipoIdentificacionComprador":
                "05",
            "./infoFactura/razonSocialComprador":
                self.proformabill.issued_to.razon_social,
            "./infoFactura/identificacionComprador":
                self.proformabill.issued_to.identificacion,
            "./infoFactura/totalSinImpuestos":
                d2(self.proformabill.total_sin_impuestos),
            "./infoFactura/totalDescuento":
                "0.00",

            # Impuestos
            "./infoFactura/totalConImpuestos/totalImpuesto[1]/codigo": "2",
            "./infoFactura/totalConImpuestos/totalImpuesto[1]/codigoPorcentaje":
                self.proformabill.items[0].iva.codigo,
            "./infoFactura/totalConImpuestos/totalImpuesto[1]/descuentoAdicional": '0.00',
            "./infoFactura/totalConImpuestos/totalImpuesto[1]/baseImponible":
                d2(self.proformabill.items[0].base_imponible_iva),
            "./infoFactura/totalConImpuestos/totalImpuesto[1]/valor":
                d2(self.proformabill.items[0].valor_iva),
            "./infoFactura/totalConImpuestos/totalImpuesto[0]/codigo": "3",
            "./infoFactura/totalConImpuestos/totalImpuesto[0]/codigoPorcentaje":
                self.proformabill.items[0].ice.codigo,
            "./infoFactura/totalConImpuestos/totalImpuesto[0]/descuentoAdicional": '0.00',
            "./infoFactura/totalConImpuestos/totalImpuesto[0]/baseImponible":
                d2(self.proformabill.items[0].base_imponible_ice),
            "./infoFactura/totalConImpuestos/totalImpuesto[0]/valor":
                d2(self.proformabill.items[0].valor_ice),

            "./infoFactura/propina": "0.00",
            "./infoFactura/importeTotal":
                d2(self.proformabill.total_con_impuestos),
            "./infoFactura/moneda": "DOLAR",

            # Detalle
            "./detalles/detalle[0]/descripcion":
                self.proformabill.items[0].description,
            "./detalles/detalle[0]/cantidad":
                d6(self.proformabill.items[0].qty),
            "./detalles/detalle[0]/precioUnitario":
                d6(self.proformabill.items[0].unit_price),
            "./detalles/detalle[0]/descuento": "0.00",
            "./detalles/detalle[0]/precioTotalSinImpuesto":
                d2(self.proformabill.items[0].total_sin_impuestos),
            # IVA item 1
            "./detalles/detalle[0]/impuestos/impuesto[1]/codigo": "2",
            "./detalles/detalle[0]/impuestos/impuesto[1]/codigoPorcentaje":
                self.proformabill.items[0].iva.codigo,
            "./detalles/detalle[0]/impuestos/impuesto[1]/tarifa":
                d2(self.proformabill.items[0].iva.porcentaje),
            "./detalles/detalle[0]/impuestos/impuesto[1]/baseImponible":
                d2(self.proformabill.items[0].base_imponible_iva),
            "./detalles/detalle[0]/impuestos/impuesto[1]/valor":
                d2(self.proformabill.items[0].valor_iva),
            # ICE item 1
            "./detalles/detalle[0]/impuestos/impuesto[0]/codigo": "3",
            "./detalles/detalle[0]/impuestos/impuesto[0]/codigoPorcentaje":
                self.proformabill.items[0].ice.codigo,
            "./detalles/detalle[0]/impuestos/impuesto[0]/tarifa":
                d2(self.proformabill.items[0].ice.porcentaje),
            "./detalles/detalle[0]/impuestos/impuesto[0]/baseImponible":
                d2(self.proformabill.items[0].base_imponible_ice),
            "./detalles/detalle[0]/impuestos/impuesto[0]/valor":
                d2(self.proformabill.items[0].valor_ice),
        }
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
                        differences.append("Difference at char {}: '{}' != '{}'".format(i, a, b))
                msg = msg + "\n" + "\n".join(differences)
            self.assertEquals(node.text, v, msg)

        # Enviar XML al SRI
        #   Esperar respuesta
        #   Si respuesta positiva
        #       Convertir proforma en final
        #       Emitir correo electronico al cliente
        #   Si no
        #       Mostrar errores


class ReportViews(LoggedInWithCompanyTests):
    """
    Checks several report views
    """
    def setUp(self):
        super(ReportViews, self).setUp()
        self.bill1 = add_instance(
            models.Bill,
            company=self.company,
            date=datetime(2015, 5, 9, 11, 30),
            number='001-001-123456789',
            xml_content='blah'*20,
            ride_content='blih'*50)
        self.bill2 = add_instance(
            models.Bill,
            company=self.company,
            date=datetime(2015, 5, 10, 11, 30),
            number='001-001-123456790',
            xml_content='blah'*20,
            ride_content='blih'*50)

    def test_daily_bills_SRI(self):
        """
        Shows a list of all the bills emitted on a day
        """
        y = 2015
        m = 5
        d = 9
        r = self.c.get(
            reverse('report_daily_bills',
                    args=(self.company.id, y, m, d)))
        self.assertEquals(
            list(r.context_data['bill_list']),
            [self.bill1])
        self.assertContains(r, "{}/{}/{}".format(d, m, y))

#    def test_weekly_bills(self):
#        """
#        Shows a list of all the bills emitted on a week
#        """
#        self.fail("TODO")

#    def test_monthly_bills(self):
#        """
#        Shows a list of all the bills emitted on a month
#        """
#        self.fail("TODO")

#    def test_monthly_ATS_annex_SRI(self):
#        """
#        Shows a helper list
#            * Anexo Transaccional Simplificado (ATS)
#        """
#        self.fail("TODO")


class PopulateBillingTest(TestCase):
    """
    Weird conditions detected with populate_billing
    """
    def test(self):
        import populate_billing
        populate_billing.print_instance = lambda a, b: None
        data = populate_billing.my_populate()

        c = Client()
        r = c.post("/accounts/login/",
                   {'username': 'javier', 'password': 'tiaputa'})
        self.assertEquals(r['location'],
                          "http://testserver" + reverse('index'))

        # It seems I can view customers and items for a different company
        urls = [
            reverse("customer_detail", args=(data['c3'].id,)),
            reverse("item_detail", args=(data['i22'].id,)),
            reverse("proformabill_detail",
                    args=(data['b3'].id,)),
        ]
        for url in urls:
            r = c.get(url)
            self.assertEquals(
                r.status_code, 404,
                "URL {} can be reached from a different user".format(url))
