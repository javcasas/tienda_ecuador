from datetime import datetime
import pytz

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

    def assertContainsObject(self, response, item, fields):
        """
        Checks all the fields in a general object
        """
        for field in fields:
            self.assertContains(response, getattr(item, field))


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
        self.ob = self.cls(**dict(self.data, company=self.company))
        self.ob.save()
        self.index_keys = self.data.keys()

    def test_index(self):
        """
        Tests the index
        """
        r = self.c.get(
            reverse(self.index_view, args=(self.company.id,)))
        self.assertContainsObject(r, self.ob, self.index_keys)

    def test_view(self):
        """
        Tests viewing the object
        The test passes if:
            The view shows the attributes of the object
        """
        r = self.c.get(
            reverse(self.detail_view, args=(self.company.id, self.ob.id)))
        self.assertContainsObject(r, self.ob, self.data.keys())

    def test_create_show_form(self):
        """
        Tests the form being shown.
        The test passes if:
            * All the data fields are in the form
            * There is a back link
        """
        r = self.c.get(
            reverse(self.create_view, args=(self.company.id,)),
        )
        # Fields
        for key in self.data.keys():
            self.assertContains(r, key)
        # Back link
        self.assertContains(
            r, reverse(self.index_view, args=(self.company.id,)))

    def test_create(self):
        """
        Tests creating a new object with self.data
        The test passes if:
            The object is created with the specified data
            The client is redirected to the object view
        """
        with self.new_item(self.cls) as new:
            r = self.c.post(
                reverse(self.create_view, args=(self.company.id,)),
                make_post(self.data),
            )
        self.assertRedirects(
            r, reverse(self.detail_view, args=(self.company.id, new.id)))
        self.assertObjectMatchesData(new, self.data)

    def test_create_crossed_company_denied(self):
        """
        Tests creating a new object using a crossed request
        that pretends to create a new object under a different company
        The test passes if:
            The object is created with the specified data
            The company of the object is the one specified in the URL
            The client is redirected to the object view
        """
        with self.new_item(self.cls) as new:
            r = self.c.post(
                reverse(self.create_view, args=(self.company.id,)),
                make_post(dict(self.data, company_id=self.company2.id)),
            )
        self.assertRedirects(
            r, reverse(self.detail_view, args=(self.company.id, new.id)))
        self.assertObjectMatchesData(new, self.data)
        self.assertEquals(new.company, self.company)

    def test_update_show_form(self):
        """
        Tests the form being shown.
        The test passes if:
            * All the data fields are in the form
            * The data fields contain the current values
            * There is a back link
        """
        r = self.c.get(
            reverse(self.update_view, args=(self.company.id, self.ob.id)),
        )
        # Fields
        for key in self.data.keys():
            self.assertContains(r, key)
        # Field values
        self.assertContainsObject(r, self.ob, self.data.keys())
        # Back link
        self.assertContains(
            r, reverse(self.detail_view, args=(self.company.id, self.ob.id)))

    def test_update(self):
        """
        Tests updating an object with self.newdata
        The test passes if:
            The object has the new data
            The client is redirected to the object view
        """
        r = self.c.post(
            reverse(self.update_view, args=(self.company.id, self.ob.id)),
            make_post(self.newdata),
        )
        self.assertRedirects(
            r, reverse(self.detail_view, args=(self.company.id, self.ob.id)))
        self.assertObjectMatchesData(
            self.cls.objects.get(id=self.ob.id), self.newdata)

    def test_delete(self):
        """
        Tests deleting the object
        The test passes if:
            The object is deleted
            The client is redirected to the object index
        """
        r = self.c.post(
            reverse(self.delete_view, args=(self.company.id, self.ob.id)),
            {}
        )
        self.assertRedirects(
            r, reverse(self.index_view, args=(self.company.id,)))
        with self.assertRaises(self.cls.DoesNotExist):
            self.cls.objects.get(id=self.ob.id)

    def test_not_logged_in_access_denied(self):
        """
        Tests that no url can be reached without authentication
        """
        urls = [
            reverse(self.index_view, args=(self.company.id,)),
            reverse(self.detail_view, args=(self.company.id, self.ob.id)),
            reverse(self.create_view, args=(self.company.id,)),
            reverse(self.update_view, args=(self.company.id, self.ob.id)),
            reverse(self.delete_view, args=(self.company.id, self.ob.id)),
        ]
        # Test get
        for url in urls:
            r = Client().get(url)
            msg = "Url {} can be GETted without authentication".format(url)
            self.assertEqual(r.status_code, 302, msg)
            self.assertRedirects(r, "/accounts/login/?next={}".format(url))
        # Test post
        for url in urls:
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
        urls = [
            reverse(self.index_view, args=(self.company.id,)),
            reverse(self.detail_view, args=(self.company.id, self.ob.id)),
            reverse(self.create_view, args=(self.company.id,)),
            reverse(self.update_view, args=(self.company.id, self.ob.id)),
            reverse(self.delete_view, args=(self.company.id, self.ob.id)),
        ]
        # Test get
        for url in urls:
            r = c.get(url)
            msg = "Url {} can be GETted from a different user".format(url)
            self.assertEqual(r.status_code, 404, msg)
        # Test post
        for url in urls:
            r = c.post(url, {})
            msg = "Url {} can be POSTed from a different user".format(url)
            # Some posts fail with method not allowed
            self.assertIn(r.status_code, [404, 405], msg)


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
            "identificacion": "1234567890",
            "email": "a@b.com",
            "direccion": "blebla street"}
    newdata = {'razon_social': 'Wis',
               "tipo_identificacion": "ruc",
               "identificacion": "1234567890001",
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
            'description': 'Item 1 description'}
    newdata = {'sku': 'P12345',
               'name': 'Item 2',
               'unit_cost': 3,
               'unit_price': 6,
               'description': 'Item 2 description'}

    def setUp(self):
        super(LoggedInWithItemTests, self).setUp()
        iva = add_instance(models.Iva,
                           descripcion="12%", codigo='12', porcentaje=12.0)
        ice = add_instance(models.Ice,
                           descripcion="Bebidas gaseosas", grupo=1,
                           codigo='3051', porcentaje=50.0)
        self.data['iva'] = self.newdata['iva'] = iva
        self.data['ice'] = self.newdata['ice'] = ice
        self.make_object()
        self.index_keys = ['sku', 'name']


class ProformaBillTests(LoggedInWithCompanyTests):
    """
    Logged in user that is associated with a company
    Has company and items
    """
    entity = 'proforma'
    cls = models.ProformaBill

    def prepare_dict(self, d):
        def try_call(f):
            if callable(f):
                return f()
            else:
                return f
        return {k: try_call(f) for k, f in d.iteritems()}

    def setUp(self):
        super(self.__class__, self).setUp()
        self.customer_data = {
            'razon_social': 'Pepe',
            "tipo_identificacion": "cedula",
            "identificacion": "1234567890",
            "email": "a@b.com",
            "direccion": "blebla street",
        }
        self.new_customer_data = {
            'razon_social': 'Wis',
            "tipo_identificacion": "ruc",
            "identificacion": "1234567890001",
            "email": "a@d.com",
            "direccion": "pupu street",
        }
        self.data = {
            'number': '001-002-1234567890',
            'date': get_date(),
        }
        self.new_data = {
            'number': '002-004-0987654321',
            'date': get_date(),
        }
        self.customer = add_instance(models.Customer,
                                     **dict(self.customer_data,
                                            company=self.company))
        self.new_customer = add_instance(models.Customer,
                                         **dict(self.new_customer_data,
                                                company=self.company))

        self.proformabill = add_instance(
            models.ProformaBill,
            **dict(self.data, company=self.company, issued_to=self.customer)
        )
        iva = add_instance(models.Iva,
                           descripcion="12%", codigo="2", porcentaje=12.0)
        ice = add_instance(models.Ice,
                           descripcion="Bebidas gaseosas", grupo=1,
                           codigo=1000, porcentaje=50)
        self.items = []
        for i in range(5):
            self.items.append(
                add_instance(
                    models.ProformaBillItem,
                    sku="SKU00{}".format(i),
                    name='Item {}'.format(i),
                    description='Description of item {}'.format(i),
                    qty=3+i,
                    iva=iva,
                    ice=ice,
                    unit_cost=5,
                    unit_price=12,
                    proforma_bill=self.proformabill))

    def test_proformabill_index(self):
        """
        Check the proforma bill index view
        """
        r = self.c.get(reverse('proformabill_index', args=(self.company.id,)))
        self.assertContainsObject(
            r, self.proformabill, ['number', 'issued_to'])
        # Edit link
        self.assertContains(
            r, reverse('proformabill_detail',
                       args=(self.company.id, self.proformabill.id)))

    def test_proformabill_detail(self):
        """
        Check the proforma bill detail view
        """
        r = self.c.get(
            reverse('proformabill_detail',
                    args=(self.company.id, self.proformabill.id)))
        self.assertContainsObject(r, self.proformabill,
                                  fix_keys(self.data.keys()))
        for item in self.items:
            self.assertContainsObject(r, item, ['sku', 'name', 'qty'])

    def test_proformabill_create_show_form(self):
        """
        Check the proforma bill creation view
        """
        r = self.c.get(reverse('proformabill_create', args=(self.company.id,)))
        for field in ['number', 'issued_to']:
            self.assertContains(r, field)

    def test_proformabill_create_submit(self):
        """
        Check the proforma bill creation view
        """
        proformabill_data = {
            'number': '6666',
            'date': get_date(),
        }
        customer, created = models.Customer.objects.get_or_create(
            **dict(self.customer_data, company=self.company))
        with self.new_item(self.cls) as new:
            r = self.c.post(
                reverse('proformabill_create', args=(self.company.id,)),
                make_post(dict(proformabill_data, issued_to=customer.id)),
            )
        self.assertRedirects(
            r, reverse('proformabill_detail', args=(self.company.id, new.id)))
        self.assertObjectMatchesData(new, proformabill_data)
        self.assertObjectMatchesData(new.issued_to, self.customer_data)

    def test_proformabill_update_show_form(self):
        """
        Check the proforma bill update view
        """
        r = self.c.get(
            reverse('proformabill_update',
                    args=(self.company.id, self.proformabill.id)))
        self.assertContainsObject(r, self.customer,
                                  ['razon_social', 'identificacion'])
        self.assertContainsObject(r, self.proformabill,
                                  fix_keys(self.data.keys()))

    def test_proformabill_update_submit(self):
        """
        Check the proforma bill update view
        """
        r = self.c.post(
            reverse('proformabill_update',
                    args=(self.company.id, self.proformabill.id)),
            make_post(dict(self.new_data, issued_to=self.new_customer.id)))
        self.assertRedirects(
            r, reverse('proformabill_detail',
                       args=(self.company.id, self.proformabill.id)))
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
                    args=(self.company.id, self.proformabill.id)))
        self.assertContains(r, self.proformabill.number)
        self.assertContains(r, self.proformabill.issued_to.razon_social)

    def test_proformabill_delete_submit(self):
        """
        Tests deleting the object
        The test passes if:
            The object is deleted
            The client is redirected to the object index
        """
        r = self.c.post(
            reverse("proformabill_delete",
                    args=(self.company.id, self.proformabill.id)),
            {}
        )
        self.assertRedirects(
            r, reverse("proformabill_index", args=(self.company.id,)))
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
            "identificacion": "1234567890",
            "email": "a@b.com",
            "direccion": "blebla street",
        }
        self.proformabill_data = {
            'number': '001-002-1234567890',
            'date': get_date(),
        }
        self.customer = add_instance(models.Customer,
                                     **dict(self.customer_data,
                                            company=self.company))
        self.proformabill = add_instance(
            models.ProformaBill,
            **dict(self.proformabill_data,
                   company=self.company, issued_to=self.customer)
        )
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
            iva=self.iva,
            ice=self.ice,
            unit_cost=5.3,
            unit_price=8,
            description='Item3 description')
        self.item = add_instance(
            models.Item,
            **dict(self.item_data, company=self.company))
        self.proformabill_item_data = dict(
            sku="SKU001",
            name='Item 1',
            description='Description of item 1',
            iva=self.iva,
            ice=self.ice,
            unit_cost=9.1,
            unit_price=16,
            qty=3)
        self.proformabill_item = add_instance(
            models.ProformaBillItem,
            **dict(self.proformabill_item_data,
                   proforma_bill=self.proformabill))

    def test_add_item_to_bill_show_form(self):
        r = self.c.get(
            reverse('proformabill_add_item',
                    args=(self.company.id, self.proformabill.id)))
        self.assertContainsObject(r, self.item, ['sku', 'name'])


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
            reverse("customer_detail", args=(data['t1'].id, data['c3'].id,)),
            reverse("item_detail", args=(data['t1'].id, data['i22'].id,)),
            reverse("proformabill_detail",
                    args=(data['t1'].id, data['b3'].id,)),
        ]
        for url in urls:
            r = c.get(url)
            self.assertEquals(
                r.status_code, 404,
                "URL {} can be reached from a different user".format(url))
