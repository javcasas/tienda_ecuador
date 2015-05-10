from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from billing import models


#class BillingIndexViewTests(TestCase):
#
#    def test_index_view(self):
#        """
#        """
#        response = self.client.get(reverse('index'))
#        self.assertEqual(response.status_code, 200)
#        self.assertContains(response, "There are no categories present.")
#        self.assertQuerysetEqual(response.context['categories'], [])

#class ItemViewTests(TestCase):
#    def test_non_existing_item_view(self):
#        """
#        Ensure a non-existing item returns a 404
#        """
#        response = self.client.get(reverse('view_item', args=(555,)))
#        self.assertEqual(response.status_code, 404)

class NotLoggedInTests(TestCase):
    """
    Ensure no useful information can be get without logging in
    """
    def test_index(self):
        response = self.client.get(reverse('index'))
        self.assertEqual(response.status_code, 302)

    def test_company_index(self):
        response = self.client.get(reverse('company_index', kwargs={'company_id': 1}))
        self.assertEqual(response.status_code, 302)


class LoggedInTests(TestCase):
    """
    Tests that support a logged-in user
    """
    def setUp(self):
        self.user = User(username="paco")
        self.user.set_password("paco_pw")
        self.user.save()
        self.c = Client()
        r = self.c.post("/accounts/login/", {'username': 'paco', 'password': 'paco_pw'})
        self.assertEquals(r.status_code, 302)  # redirect to index

    def tearDown(self):
        self.user.delete()

class ViewLoggedInTests(LoggedInTests):
    def setUp(self):
        super(ViewLoggedInTests, self).setUp()
        self.company = models.Company(name='Tienda 1')
        self.company.save()
        self.companyuser = models.CompanyUser(user=self.user, company=self.company)
        self.companyuser.save()

    def tearDown(self):
        self.companyuser.delete()
        self.company.delete()
        super(ViewLoggedInTests, self).tearDown()

    def test_view_index(self):
        """
        A logged-in user can view the billing index, and the index shows the available companies
        """
        response = self.c.get(reverse('index'))
        self.assertEquals(response.status_code, 200)
        self.assertEquals(list(response.context['companies']), [self.company])
        self.assertContains(response, self.company.name)
