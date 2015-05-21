from django.test import TestCase, Client
from django.core.urlresolvers import reverse

from billing import models

from helpers import (add_Company,
                     add_CompanyUser,
                     add_User, TestHelpersMixin,
                     add_instance,
                     make_post)


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
        self.company = add_Company(name='Tienda 1',
                                   sri_razon_social='Paco Pil',
                                   sri_ruc='1234567890')
        self.company_user = add_CompanyUser(user=self.user,
                                            company=self.company)


class IndexViewTests(LoggedInWithCompanyTests):
    def test_view_index_multiple_companies(self):
        """
        A logged-in user can view the billing index,
        and the index shows the available companies
        """
        company2 = add_Company(name="Tienda 2")
        add_CompanyUser(user=self.user, company=company2)

        response = self.c.get(reverse('index'))
        self.assertEquals(response.status_code, 200)

        for c in [self.company, company2]:
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
        self.assertContains(r, self.company.name)

    def test_view_company_index_access_denied(self):
        """
        A logged-in user can't view the index for a company he has no access
        """
        company2 = add_Company(name="Tienda 2")
        response = self.c.get(
            reverse('company_index', args=(company2.id,))
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

    def test_index(self):
        """
        Tests the index
        """
        r = self.c.get(
            reverse(self.index_view, args=(self.company.id,)))
        self.assertContainsObject(r, self.ob, self.data.keys())

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
        company2 = add_Company(name='Tienda2')
        with self.new_item(self.cls) as new:
            r = self.c.post(
                reverse(self.create_view, args=(self.company.id,)),
                make_post(dict(self.data, company_id=company2.id)),
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
            r = Client().post(url, {})
            msg = "Url {} can be POSTed without authentication".format(url)
            self.assertEqual(r.status_code, 302, msg)
            self.assertRedirects(r, "/accounts/login/?next={}".format(url))


class LoggedInWithCustomerTests(LoggedInWithCompanyTests,
                                GenericObjectCRUDTest):
    """
    Logged in user that is associated with a company
    Has company and customers
    """
    entity = 'customer'
    cls = models.Customer
    data = {'name': 'Pepe'}
    newdata = {'name': 'Wis'}

    def setUp(self):
        super(LoggedInWithCustomerTests, self).setUp()
        self.make_object()


class LoggedInWithItemTests(LoggedInWithCompanyTests, GenericObjectCRUDTest):
    """
    Logged in user that is associated with a company
    Has company and items
    """
    entity = 'item'
    cls = models.Item
    data = {'sku': 'P1234',
            'name': 'Item 1',
            'description': 'Item 1 description'}
    newdata = {'sku': 'P12345',
               'name': 'Item 2',
               'description': 'Item 2 description'}

    def setUp(self):
        super(LoggedInWithItemTests, self).setUp()
        self.make_object()

from unittest import skip
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
        self.data = {'issued_to': lambda: add_instance(models.Customer, name="Pepe", company=self.company),
                'number': '001-002-1234567890',}
        self.newdata = {'number': '002-004-0987654321',
                   'issued_to': lambda: add_instance(models.Customer, name="Paco", company=self.company),}
        self.proforma_bill = add_instance(
            models.ProformaBill,
            **dict(self.prepare_dict(self.data), company=self.company)
        )
        self.items = []
        for i in range(5):
            self.items.append(
                add_instance(
                    models.ProformaBillItem,
                    sku="SKU00{}".format(i),
                    name='Item {}'.format(i),
                    description='Description of item {}'.format(i),
                    qty=3+i,
                    proforma_bill=self.proforma_bill))

    def test_proformabill_index(self):
        """
        Check the proforma bill index view
        """
        r = self.c.get(reverse('proformabill_index', args=(self.company.id,)))
        self.assertContainsObject(r, self.proforma_bill, ['number', 'issued_to'])
        # Edit link
        self.assertContains(r, reverse('proformabill_detail', args=(self.company.id, self.proforma_bill.id)))

    def test_proformabill_detail(self):
        """
        Check the proforma bill detail view
        """
        r = self.c.get(reverse('proformabill_detail', args=(self.company.id, self.proforma_bill.id)))
        self.assertContainsObject(r, self.proforma_bill, self.data.keys())
        for item in self.items:
            self.assertContainsObject(r, item, ['sku', 'name', 'qty'])

    def test_proformabill_create_show_form(self):
        """
        Check the proforma bill creation view
        """
        r = self.c.get(reverse('proformabill_create', args=(self.company.id,)))
        for field in ['number', 'issued_to']:
            self.assertContains(r, field)

    def test_proformabill_create(self):
        """
        Check the proforma bill creation view
        """
        customer_data = {
            'name': 'Roberto',
        }
        proformabill_data = {
            'number': '6666',
        }
        customer, created = models.Customer.objects.get_or_create(**dict(customer_data, company=self.company))
        with self.new_item(self.cls) as new:
            r = self.c.post(
                reverse('proformabill_create', args=(self.company.id,)),
                make_post(dict(proformabill_data, issued_to=customer.id)),
            )
        self.assertRedirects(
            r, reverse('proformabill_detail', args=(self.company.id, new.id)))
        self.assertObjectMatchesData(new, proformabill_data)
        self.assertObjectMatchesData(new.issued_to, customer_data)

    def test_proformabill_update(self):
        """
        Check the proforma bill update view
        """
        customer_data = {
            'name': 'Roberto',
        }
        proformabill_data = {
            'number': '6666',
        }
        new_proformabill_data = {
            'number': '7777',
        }
        customer, created = models.Customer.objects.get_or_create(dict(customer_data, company=self.company))
        proformabill, created = models.ProformaBill.objects.get_or_create(
            **dict(proformabill_data, issued_to=customer, company=self.company))
        r = self.c.get(
            reverse('proformabill_update', args=(self.company.id, proformabill.id)))
        self.assertContainsObject(r, customer, customer_data.keys())
        self.assertContainsObject(r, proformabill, proformabill_data.keys())
        r = self.c.post(
            reverse('proformabill_update', args=(self.company.id, proformabill.id)),
            make_post(dict(new_proformabill_data, issued_to=customer.id)))
        self.assertRedirects(
            r, reverse('proformabill_detail', args=(self.company.id, proformabill.id)))
        self.assertObjectMatchesData(models.ProformaBill.objects.get(id=proformabill.id), new_proformabill_data)
