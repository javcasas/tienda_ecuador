from functools import partial
from contextlib import contextmanager

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.core.exceptions import ObjectDoesNotExist

from billing import models

from helpers import (add_Company, add_Item, add_Customer,
                     add_CompanyUser, add_Bill, add_BillItem,
                     add_User, try_delete)


def make_post(data):
    """
    Converts a data dict into a data dict that can be used in a POST
    """
    def convert_field(f):
        try:
            return f.id
        except:
            return f
    return {k: convert_field(v) for (k, v) in data.iteritems()}


@contextmanager
def new_item(kind):
    """
    Finds and returns the new item of the specified kind
    created in the context
    """
    def get_set(model):
        return set(model.objects.all())

    class GetattrProxy(object):
        ob = None

        def __getattr__(self, field):
            return getattr(self.ob, field)

    items = get_set(kind)
    res = GetattrProxy()
    yield res
    new_items = (get_set(kind) - items)
    assert len(new_items) == 1
    res.ob = new_items.pop()


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


class LoggedInTests(TestCase):
    """
    Tests that support a logged-in user
    """
    def setUp(self):
        username, password = 'paco', 'paco_pw'
        self.user = add_User(username=username, password=password)
        self.c = Client()
        r = self.c.post("/accounts/login/",
                        {'username': username, 'password': password})
        self.assertEquals(r.status_code, 302)  # redirect to index

    def tearDown(self):
        self.user.delete()


class LoggedInWithCompanyTests(LoggedInTests):
    """
    Logged in user that is associated with a company
    """
    def setUp(self):
        super(LoggedInWithCompanyTests, self).setUp()
        self.company = add_Company(name='Tienda 1')
        self.company_user = add_CompanyUser(user=self.user,
                                            company=self.company)

    def tearDown(self):
        for i in [self.company_user, self.company]:
            try_delete(i)
        super(LoggedInWithCompanyTests, self).tearDown()


class IndexViewTests(LoggedInWithCompanyTests):
    def test_view_index_multiple_companies(self):
        """
        A logged-in user can view the billing index,
        and the index shows the available companies
        """
        try:
            company2 = add_Company(name="Tienda 2")
            company2_user = add_CompanyUser(user=self.user, company=company2)
            response = self.c.get(reverse('index'))
            self.assertEquals(response.status_code, 200)
            self.assertEquals(list(response.context['companies']),
                              [self.company, company2])
            self.assertContains(response, self.company.name)
            self.assertContains(response, company2.name)
        finally:
            for i in [company2_user, company2]:
                try_delete(i)

    def test_view_index_single_company(self):
        """
        A logged-in user is redirected if he has only a single company
        """
        response = self.c.get(reverse('index'))
        self.assertRedirects(response,
                             reverse('company_index', args=(self.company.id,)))

    def test_view_company_index_access_denied(self):
        """
        A logged-in user can't view the index for a company he has no access
        """
        try:
            company2 = add_Company(name="Tienda 2")
            response = self.c.get(
                reverse('company_index', args=(company2.id,))
            )
            self.assertEquals(response.status_code, 404)
        finally:
            for i in [company2]:
                try_delete(i)


class LoggedInWithBillsItemsTests(LoggedInWithCompanyTests):
    """
    Logged in user associated with a company that has bills and items
    """
    def setUp(self):
        """
        Adds an item, a customer, and a bill with an item
        """
        super(self.__class__, self).setUp()
        self.item = add_Item(
            sku="SKU123", name='An Item',
            description='The description', company=self.company
        )
        self.customer = add_Customer(name="Luis", company=self.company)
        self.customer2 = add_Customer(name="Paco", company=self.company)
        self.bill = add_Bill(
            issued_to=self.customer, number='001-002-123456789',
            company=self.company, is_proforma=True
        )
        self.bill_item = add_BillItem(
            sku="SKU123", name='An Item', description='The description',
            company=self.company, bill=self.bill, qty=4
        )

    def tearDown(self):
        for i in [self.bill_item, self.bill, self.customer, self.item]:
            try_delete(i)
        super(self.__class__, self).tearDown()

    def assertContainsObject(self, response, item, fields):
        """
        Checks all the fields in a general object
        """
        for field in fields:
            self.assertContains(response, getattr(item, field))

    def assertObjectMatchesData(self, ob, data):
        """
        Checks that every field in the data
        exists in the object and is the same
        """
        for key, value in data.iteritems():
            self.assertEquals(getattr(ob, key), value)

    def test_company_index(self):
        """
        Ensures the company index shows the items and the bills
        """
        response = self.c.get(
            reverse('company_index', args=(self.company.id,))
        )
        self.assertContainsObject(response, self.item, fields=['name', 'sku'])
        # View items
        self.assertContains(
            response,
            reverse('view_item', args=(self.company.id, self.item.id))
        )
        # View bills
        self.assertContains(
            response,
            reverse('view_bill', args=(self.company.id, self.bill.id))
        )
        self.assertContainsObject(response, self.bill, fields=['number'])
        self.assertContainsObject(
            response, self.bill.issued_to, fields=['name']
        )
        # View customers
        self.assertContainsObject(
            response, self.customer2, fields=['name']
        )
        

    def test_view_item(self):
        """
        Ensures the company index shows the items and the bills
        """
        response = self.c.get(
            reverse('view_item', args=(self.company.id, self.item.id))
        )
        self.assertContainsObject(response, self.item,
                                  fields=['name', 'sku', 'description'])
        self.assertContains(response,
                            reverse('edit_item', args=(self.company.id, self.item.id)))
        self.assertContains(response,
                            reverse('company_index', args=(self.company.id,)))

    def test_edit_item(self):
        """
        Ensures you can edit an item
        """
        r = self.c.get(
            reverse('edit_item', args=(self.company.id, self.item.id))
        )
        self.assertContainsObject(
            r, self.item, fields=['name', 'sku', 'description']
        )
        # Cancel/Back button/link
        self.assertContains(
            r, reverse('view_item', args=(self.company.id, self.item.id))
        )

    def test_edit_item_submit(self):
        """
        Ensures you can submit an item
        """
        data = {
            'sku': '555',
            'name': 'myitem',
            'description': 'bleh',
        }
        r = self.c.post(
            reverse('edit_item', args=(self.company.id, self.item.id)),
            make_post(data)
        )
        self.assertObjectMatchesData(
            models.Item.objects.get(id=self.item.id), data
        )
        self.assertRedirects(
            r, reverse('view_item', args=(self.company.id, self.item.id))
        )

    def test_view_bill(self):
        """
        Ensures the bills can be viewed
        """
        response = self.c.get(
            reverse('view_bill', args=(self.company.id, self.bill.id))
        )
        self.assertContains(response, self.bill.number)
        self.assertContains(response, self.bill.issued_to.name)
        for item in self.bill.items:
            self.assertContainsObject(response, item,
                                      fields=['name', 'sku', 'description'])
            self.assertContains(response,
                                reverse('edit_item_in_bill', args=(self.company.id, self.bill.id, item.id)))
            self.assertContains(response,
                                reverse('delete_item_from_bill', args=(self.company.id, self.bill.id, item.id)))
        self.assertContains(response,
                            reverse('edit_bill', args=(self.company.id, self.bill.id)))
        self.assertContains(response,
                            reverse('add_item_to_bill', args=(self.company.id, self.bill.id)))
        # Cancel/Back button/link
        self.assertContains(response,
                            reverse('company_index', args=(self.company.id,)))

    def test_edit_bill(self):
        """
        Ensures the bills can be edited
        """
        response = self.c.get(
            reverse('edit_bill', args=(self.company.id, self.bill.id))
        )
        self.assertContains(response, self.bill.number)
        self.assertContains(response, self.bill.issued_to.name)
        # Cancel/Back button/link
        self.assertContains(
            response,
            reverse('view_bill', args=(self.company.id, self.bill.id))
        )

    def test_edit_bill_submit(self):
        """
        Ensures you can submit a bill
        """
        url = reverse('edit_bill', args=(self.company.id, self.bill.id))
        data = {
            'number': '555',
            'issued_to': self.customer.id,
        }
        r = self.c.post(url, data)
        bill = models.Bill.objects.get(id=self.bill.id)
        self.assertEquals(bill.number, data['number'])
        self.assertEquals(bill.issued_to.id, data['issued_to'])
        self.assertRedirects(
            r,
            reverse('view_bill', args=(self.company.id, self.bill.id))
        )

    def test_edit_final_bill_submit(self):
        """
        Ensures you can't submit a final bill
        """
        self.bill.is_proforma = False
        self.bill.save()
        url = reverse('edit_bill', args=(self.company.id, self.bill.id))
        number = '555'
        issued_to = self.customer.id
        r = self.c.post(url, {
            'number': number,
            'issued_to': issued_to,
        })
        self.assertEquals(r.status_code, 403)  # Forbidden

    def test_new_bill(self):
        """
        Ensures you can create a new bill using a POST
        """
        with new_item(models.Bill) as new:
            r = self.c.post(
                reverse('new_bill', args=(self.company.id,)),
                {}
            )
        self.assertEquals(new.issued_to.name, 'Consumidor Final')
        self.assertRedirects(
            r, reverse('view_bill', args=(self.company.id, new.id)))

    def test_delete_bill(self):
        """
        Ensures you can delete a proforma bill using a POST
        """
        url = reverse('delete_bill', args=(self.company.id, self.bill.id))
        r = self.c.post(url, {})
        self.assertFalse(models.Bill.objects.filter(id=self.bill.id))
        self.assertRedirects(
            r, reverse('company_index', args=(self.company.id,)))

    def test_delete_final_bill(self):
        """
        Ensures you can't delete a final bill
        """
        self.bill.is_proforma = False
        self.bill.save()
        url = reverse('delete_bill', args=(self.company.id, self.bill.id))
        r = self.c.post(url, {})
        self.assertTrue(models.Bill.objects.filter(id=self.bill.id))
        self.assertEquals(r.status_code, 403)  # Forbidden

    def test_add_item_to_bill(self):
        """
        Ensures you can select items to add to bills
        """
        url = reverse('add_item_to_bill', args=(self.company.id, self.bill.id))
        r = self.c.get(url)
        self.assertEquals(r.status_code, 200)
        # for item in models.Item.objects.filter(company=self.company):
        #    self.assertContainsObject(r, item,
        #                              fields=['name', 'sku', 'description'])

    def test_add_item_to_bill_submit(self):
        """
        Ensures you can add items to bills
        """
        data = {
            'sku': '555',
            'name': 'myitem',
            'description': 'bleh',
            'qty': 44,
            'bill': self.bill,
            'company': self.company,
        }
        with new_item(models.BillItem) as new:
            r = self.c.post(
                reverse('add_item_to_bill',
                        args=(self.company.id, self.bill.id)),
                make_post(data)
            )
        self.assertRedirects(
            r, reverse('view_bill', args=(self.company.id, self.bill.id)))
        self.assertObjectMatchesData(new, data)

    def test_add_item_to_final_bill_submit(self):
        """
        Ensures you can't add items to final bills
        """
        self.bill.is_proforma = False
        self.bill.save()
        data = {
            'sku': '555',
            'name': 'myitem',
            'description': 'bleh',
            'qty': 44,
            'bill': self.bill,
            'company': self.company,
        }
        r = self.c.post(
            reverse('add_item_to_bill', args=(self.company.id, self.bill.id)),
            make_post(data)
        )
        self.assertEquals(r.status_code, 403)

    def test_add_item_to_final_bill(self):
        """
        Ensures you can't add items to final bills
        """
        self.bill.is_proforma = False
        self.bill.save()
        url = reverse('add_item_to_bill', args=(self.company.id, self.bill.id))
        r = self.c.get(url)
        self.assertEquals(r.status_code, 403)

    def test_edit_item_in_bill(self):
        """
        Ensures you can edit items in a bill
        """
        r = self.c.get(
            reverse('edit_item_in_bill',
                    args=(self.company.id, self.bill.id, self.bill_item.id))
        )
        self.assertEquals(r.status_code, 200)
        self.assertContainsObject(
            r, self.bill_item, fields=['name', 'sku', 'description'])
        # Back/Cancel link
        self.assertContains(
            r, reverse('view_bill', args=(self.company.id, self.bill.id)))

    def test_edit_item_in_bill_submit(self):
        """
        Ensures you can edit and submit items to bills
        """
        data = {
            'sku': '555',
            'name': 'myitem',
            'description': 'bleh',
            'qty': 44,
            'bill': self.bill,
            'company': self.company,
        }
        r = self.c.post(
            reverse('edit_item_in_bill',
                    args=(self.company.id, self.bill.id, self.bill_item.id)),
            make_post(data)
        )
        self.assertRedirects(
            r, reverse('view_bill', args=(self.company.id, self.bill.id)))
        bill_item = models.BillItem.objects.get(id=self.bill_item.id)
        self.assertObjectMatchesData(bill_item, data)

    def test_edit_item_in_final_bill(self):
        """
        Ensures you can't edit items in a final bill
        """
        self.bill.is_proforma = False
        self.bill.save()
        r = self.c.get(
            reverse('edit_item_in_bill',
                    args=(self.company.id, self.bill.id, self.bill_item.id))
        )
        self.assertEquals(r.status_code, 403)

    def test_edit_item_in_final_bill_submit(self):
        """
        Ensures you can't edit and submit items to bills
        """
        self.bill.is_proforma = False
        self.bill.save()
        data = {
            'sku': '555',
            'name': 'myitem',
            'description': 'bleh',
            'qty': 44,
            'bill': self.bill,
            'company': self.company,
        }
        r = self.c.post(
            reverse('edit_item_in_bill',
                    args=(self.company.id, self.bill.id, self.bill_item.id)),
            make_post(data)
        )
        self.assertEquals(r.status_code, 403)

    def test_delete_item_from_bill(self):
        """
        Ensures you can delete an item in a proforma bill using a POST
        """
        r = self.c.post(
            reverse('delete_item_from_bill',
                    args=(self.company.id, self.bill.id, self.bill_item.id)),
            {}
        )
        self.assertRedirects(
            r, reverse('view_bill', args=(self.company.id, self.bill.id)))
        self.assertFalse(models.BillItem.objects.filter(id=self.bill_item.id))

    def test_delete_item_from_final_bill(self):
        """
        Ensures you can't delete an item in a final bill
        """
        self.bill.is_proforma = False
        self.bill.save()
        r = self.c.post(
            reverse('delete_item_from_bill',
                    args=(self.company.id, self.bill.id, self.bill_item.id)),
            {}
        )
        self.assertTrue(models.Bill.objects.filter(id=self.bill.id))
        self.assertEquals(r.status_code, 403)  # Forbidden

    def test_get_not_allowed(self):
        """
        Ensures GET methods do nothing for some URLs
        """
        urls = [
            reverse('delete_item_from_bill',
                    args=(self.company.id, self.bill.id, self.bill_item.id)),
            reverse('new_bill', args=(self.company.id,)),
            reverse('delete_bill', args=(self.company.id, self.bill.id)),
        ]
        for url in urls:
            r = self.c.get(url)
            self.assertEquals(r.status_code, 405)

    def test_access_denied(self):
        """
        A logged-in user can't view stuff for a company he has no access
        """
        username, password = 'pepe', 'pepe_pw'
        user = add_User(username=username, password=password)
        c = Client()
        r = c.post("/accounts/login/",
                   {'username': username, 'password': password})
        self.assertEquals(r.status_code, 302)  # redirect to index

        # URLs to check
        urls = [
            reverse('company_index', args=(self.company.id,)),
            reverse('view_item', args=(self.company.id, self.item.id)),
            reverse('edit_item', args=(self.company.id, self.item.id)),
            reverse('view_bill', args=(self.company.id, self.bill.id)),
            reverse('edit_bill', args=(self.company.id, self.bill.id)),
            reverse('new_bill', args=(self.company.id,)),
            reverse('delete_bill', args=(self.company.id, self.bill.id)),
            reverse('add_item_to_bill', args=(self.company.id, self.bill.id)),
            reverse('edit_item_in_bill',
                    args=(self.company.id, self.bill.id, self.bill_item.id)),
            reverse('delete_item_from_bill',
                    args=(self.company.id, self.bill.id, self.bill_item.id)),
        ]
        try:
            for url in urls:
                response = c.get(url)
                self.assertEquals(
                    response.status_code, 404,
                    "URL {} can be checked from another user".format(url)
                )
        finally:
            for i in [user]:
                try_delete(i)
