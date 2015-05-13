from functools import partial

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.core.exceptions import ObjectDoesNotExist

from billing import models


def add_instance(klass, **kwargs):
    """
    Add a instance of the specified class with the specified arguments,
    and returns it after saving it
    """
    s = klass.objects.get_or_create(**kwargs)[0]
    s.save()
    return s


add_Company = partial(add_instance, models.Company)
add_Item = partial(add_instance, models.Item)
add_Customer = partial(add_instance, models.Customer)
add_CompanyUser = partial(add_instance, models.CompanyUser)
add_Bill = partial(add_instance, models.Bill)
add_BillItem = partial(add_instance, models.BillItem)


def add_User(**kwargs):
    pw = kwargs.pop("password")
    u = add_instance(User, **kwargs)
    u.set_password(pw)
    u.save()
    return u


def try_delete(item):
    try:
        if item.pk:
            item.delete()
    except ObjectDoesNotExist:
        pass


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
        self.customer = add_Customer(name="Luis")
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

    def test_company_index(self):
        """
        Ensures the company index shows the items and the bills
        """
        response = self.c.get(
            reverse('company_index', args=(self.company.id,))
        )
        self.assertContains(response, self.item.name)
        self.assertContains(response, self.item.sku)
        # View item link
        self.assertContains(response, reverse('view_item', args=(self.company.id, self.item.id)))
        self.assertContains(response, self.bill.number)
        self.assertContains(response, self.bill.issued_to.name)
        # View bill link
        self.assertContains(response, reverse('view_bill', args=(self.company.id, self.bill.id)))

    def assertContainsItem(self, response, item):
        """
        Checks all the fields in an item
        """
        self.assertContains(response, self.item.name)
        self.assertContains(response, self.item.sku)
        self.assertContains(response, self.item.description)

    def test_view_item(self):
        """
        Ensures the company index shows the items and the bills
        """
        response = self.c.get(
            reverse('view_item', args=(self.company.id, self.item.id))
        )
        self.assertContainsItem(response, self.item)
        self.assertContains(response, reverse('company_index', args=(self.company.id,)))

    def test_edit_item(self):
        """
        Ensures you can edit an item
        """
        url = reverse('edit_item', args=(self.company.id, self.item.id))
        response = self.c.get(url)
        self.assertContainsItem(response, self.item)
        # Cancel/Back button/link
        self.assertContains(response, reverse('view_item', args=(self.company.id, self.item.id)))

    def test_edit_item_submit(self):
        """
        Ensures you can submit an item
        """
        url = reverse('edit_item', args=(self.company.id, self.item.id))
        sku = '555'
        name = 'myitem'
        description = 'bleh'
        r = self.c.post(url, {
            'sku': sku,
            'name': name,
            'description': description
        })
        item = models.Item.objects.get(id=self.item.id)
        self.assertEquals(item.sku, sku)
        self.assertEquals(item.name, name)
        self.assertEquals(item.description, description)
        self.assertRedirects(r,  reverse('view_item', args=(self.company.id, self.item.id)))

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
            self.assertContainsItem(response, item)
        # Cancel/Back button/link
        self.assertContains(response, reverse('company_index', args=(self.company.id,)))

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
        self.assertContains(response, reverse('view_bill', args=(self.company.id, self.bill.id)))

    def test_edit_bill_submit(self):
        """
        Ensures you can submit a bill
        """
        url = reverse('edit_bill', args=(self.company.id, self.bill.id))
        number = '555'
        issued_to = self.customer.id
        r = self.c.post(url, {
            'number': number,
            'issued_to': issued_to,
        })
        bill = models.Bill.objects.get(id=self.bill.id)
        self.assertEquals(bill.number, number)
        self.assertEquals(bill.issued_to.id, issued_to)
        self.assertRedirects(r,  reverse('view_bill', args=(self.company.id, self.bill.id)))

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
        bill = models.Bill.objects.get(id=self.bill.id)
        self.assertEquals(r.status_code, 403)  # Forbidden

    def test_new_bill(self):
        """
        Ensures you can create a new bill using a POST
        """
        bills = set(models.Bill.objects.all())
        url = reverse('new_bill', args=(self.company.id,))
        r = self.c.post(url, {})
        new_bills = set(models.Bill.objects.all())
        new_bill = (new_bills - bills).pop()
        self.assertEquals(new_bill.issued_to.name, 'Consumidor Final')
        self.assertRedirects(r,  reverse('view_bill', args=(self.company.id, new_bill.id)))

    def test_new_bill_get(self):
        """
        Ensures GET fails to create a new bill
        """
        r = self.c.get(reverse('new_bill', args=(self.company.id,)))
        self.assertEquals(r.status_code, 405)

    def test_delete_bill(self):
        """
        Ensures you can delete a proforma bill using a POST
        """
        url = reverse('delete_bill', args=(self.company.id, self.bill.id))
        r = self.c.post(url, {})
        self.assertFalse(models.Bill.objects.filter(id=self.bill.id))
        self.assertRedirects(r,  reverse('company_index', args=(self.company.id,)))

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

    def test_delete_bill_get(self):
        """
        Ensures GET fails to delete a bill
        """
        r = self.c.get(reverse('delete_bill', args=(self.company.id, self.bill.id)))
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
