# * encoding: utf-8 *
from datetime import datetime, date, timedelta
import pytz
import json

from django.test import TestCase, Client
from django.core.urlresolvers import reverse
from django.http.response import HttpResponseRedirect

from company_accounts import models, views

from util.testsuite.helpers import (TestHelpersMixin,
                                    add_instance,
                                    add_User,
                                    make_post)

from test_models import MakeBaseInstances


def get_date():
    now = datetime.now(tz=pytz.timezone('America/Guayaquil'))
    return now.replace(microsecond=0)


def fix_keys(keys):
    bad_keys = ['date']
    return [k for k in keys if k not in bad_keys]


class NotLoggedInTests(object):
    """
    Ensure no useful information can be get without logging in
    """
    def test_index(self):
        response = self.client.get(reverse('company_accounts:company_select'))
        self.assertEqual(response.status_code, 302)

    def test_company_index(self):
        response = self.client.get(
            reverse('company_index', kwargs={'company_id': 1})
        )
        self.assertEqual(response.status_code, 302)


class LoggedInTests(object):
    """
    Tests that support a logged-in user
    """
    def setUp(self):
        super(LoggedInTests, self).setUp()
        self.c = Client()
        r = self.c.post("/accounts/login/",
                        {'username': self.user.username,
                         'password': "paco_pw"},
                        follow=True)
        self.assertRedirects(r, reverse('company_accounts:company_main_menu',
                                        args=(self.company.id,)))

    def tearDown(self):
        self.assert_no_broken_urls()
        super(LoggedInTests, self).tearDown()

    def assert_no_broken_urls(self):
        for model in self.__dict__.values():
            try:
                obs = model.objects.all
                for ob in obs:
                    ob.get_absolute_url()
            except AttributeError:
                # Not a model, or no absolute URL
                continue
            for ob in obs:
                r = self.c.get(ob.get_absolute_url())
                self.assertIn(r.status_code, [200, 404, 405])

#     def assertContainsObject(self, response, item, fields, msg=None):
#         """
#         Checks all the fields in a general object
#         """
#         for field in fields:
#             value = getattr(item, field)
#             self.assertContains(
#                 response, str(value), html=False,
#                 msg_prefix='Field {} ({}) not found'.format(field, value))
#
#     def simulate_post(self, url, data_to_post, client=None, form_index=0):
#         """
#         Simulates a post
#             Only commits data that is not in hidden fields
#         """
#         client = client or self.c
#         source_html = client.get(url).content
#         try:
#             root = ET.fromstring(source_html)
#         except:
#             open("test.xml", "w").write(source_html)
#             raise
#         data_to_post = make_post(data_to_post)
#         data_to_use = {}
#
#         current_form = root.findall(".//form")[form_index]
#         # input fields, including hidden inputs
#         for i in current_form.findall(".//input"):
#             key = i.get('name')
#             pre_value = i.get('value')
#             type_ = i.get('type')
#             # Pre-filled in values
#             data_to_use[key] = pre_value or ""
#             # Added values
#             if type_ != "hidden" and data_to_post.get(key):
#                 data_to_use[key] = data_to_post.pop(key)
#             if type_ == 'hidden' and data_to_post.get(key):
#                 self.fail(
#                     "Test error: Attempt to post custom"
#                     " value for hidden field: {} = {}".format(
#                         key, data_to_post[key]))
#
#         # textarea fields
#         textareas = root.findall(".//form//textarea")
#         for ta in textareas:
#             key = ta.get('name')
#             data_to_use[key] = data_to_post.pop(key, ta.text)
#
#         # select fields
#         selects = root.findall(".//form//select")
#         for s in selects:
#             key = s.get('name')
#             selected_option = root.findall(
#                 ".//form//select[@name='{}']"
#                 "/option[@selected]".format(key))
#             default = selected_option[0].get("value") if selected_option else ""
#             data_to_use[key] = data_to_post.pop(key, default)
#
#         self.assertFalse(data_to_post, "Items left in data to post: {}".format(data_to_post))
#         return client.post(url, data_to_use)


class LoggedInWithCompanyTests(LoggedInTests):
    """
    Logged in user that is associated with a company
    """
#     def setUp(self):
#         super(LoggedInWithCompanyTests, self).setUp()
#         self.company = add_instance(
#             models.Company,
#             nombre_comercial='Tienda 1',
#             ruc='1234567890',
#             razon_social='Paco Pil',
#             direccion_matriz="C del pepino")
#         self.company_user = add_instance(
#             models.CompanyUser,
#             user=self.user,
#             company=self.company)
#         self.company2 = add_instance(
#             models.Company,
#             nombre_comercial='Tienda 2',
#             ruc='1234567892',
#             razon_social='Paca Pil',
#             direccion_matriz="C del pepano")
#
#         self.establecimiento = add_instance(
#             models.Establecimiento,
#             company=self.company,
#             descripcion="Matriz",
#             direccion='C del pepino',
#             codigo="001",
#         )
#
#         self.punto_emision = add_instance(
#             models.PuntoEmision,
#             establecimiento=self.establecimiento,
#             descripcion="Caja de la matriz",
#             codigo="001"
#         )


class IndexViewTests(LoggedInTests, MakeBaseInstances, TestCase):
    def setUp(self):
        super(IndexViewTests, self).setUp()
        self.company2 = add_instance(
            models.Company,
            nombre_comercial='Tienda 2',
            ruc='1234567892',
            razon_social='Paca Pil',
            direccion_matriz="C del pepano")

    def test_view_index_multiple_companies(self):
        """
        A logged-in user can view the billing index,
        and the index shows the available companies
        """
        add_instance(models.CompanyUser,
                     user=self.user,
                     company=self.company2)

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
                          "http://testserver" + reverse('billing_index'))
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
                          "http://testserver" + reverse('billing_index'))

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


class LicenceTests(TestCase):
    """
    Logged in user that is associated with a company
    """
    def setUp(self):
        username, password = 'paco', 'paco_pw'
        self.user = add_User(username=username, password=password)

        self.company = add_instance(
            models.Company,
            nombre_comercial='Tienda 1',
            ruc='1234567890',
            razon_social='Paco Pil',
            direccion_matriz="C del pepino")

        self.company_user = add_instance(
            models.CompanyUser,
            user=self.user,
            company=self.company)

    def test_valid_licence(self):
        self.assertTrue(
            views.valid_licence(self.user, ['demo']))
        self.assertFalse(
            views.valid_licence(self.user, ['basic']))

    def test_licence_required(self):
        @views.licence_required("professional")
        class TestView(object):
            def dispatch(self, request):
                raise Exception('blah')

        class Request(object):
            pass

        t = TestView()
        r = Request()
        r.user = self.user
        res = t.dispatch(r)

        self.assertEquals(
            type(res),
            HttpResponseRedirect)
        self.assertEquals(res.url, reverse("pricing"))

        self.company.licence.approve('professional', date(2020, 12, 12))
        with self.assertRaises(Exception):
            print t.dispatch(r)


class LicenceActivateViewTests(LoggedInTests, MakeBaseInstances, TestHelpersMixin, TestCase):
    """
    Tests for testing automated licence approval
    """
    def test_demo_licence(self):
        """
        A demo licence is properly shown on the profile page
        """
        r = self.c.get(reverse("company_accounts:company_profile", args=(self.company.id,)))
        self.assertContains(r, "Modo Demo")

    def test_nonpaid_basic_licence(self):
        """
        We select a licence, but do not pay it
        """
        r = self.c.get(reverse("company_accounts:company_profile_select_plan", args=(self.company.id,)))
        self.assertContains(r, "Basic")
        self.assertContains(r, "Professional")
        self.assertContains(r, "Enterprise")

        r = self.c.post(
            reverse("company_accounts:company_profile_select_plan", args=(self.company.id,)),
            {'selected_plan': 'basic'})
        self.assertRedirects(r, reverse("company_accounts:company_profile", args=(self.company.id,)))

        r = self.c.get(reverse("company_accounts:company_profile", args=(self.company.id,)))
        self.assertContains(r, "<td>Basic</td>")
        self.assertContains(r, "Licencia Caducada")

    def test_paid_basic_licence(self):
        """
        We select a licence and pay it
        """
        r = self.c.get(reverse("company_accounts:company_profile_select_plan", args=(self.company.id,)))
        self.assertContains(r, "Basic")
        self.assertContains(r, "Professional")
        self.assertContains(r, "Enterprise")

        r = self.c.post(
            reverse("company_accounts:company_profile_select_plan", args=(self.company.id,)),
            {'selected_plan': 'basic'})
        self.assertRedirects(r, reverse("company_accounts:company_profile", args=(self.company.id,)))

        r = self.c.get(reverse("company_accounts:company_profile", args=(self.company.id,)))
        self.assertContains(r, "<td>Basic</td>")
        self.assertContains(r, "Licencia Caducada")
        self.assertContains(r, "Renovar Licencia")  # Link to payment
        self.assertContains(r, reverse("company_accounts:pay_licence", args=(self.company.id,)))
        self.assertEquals(self.company.licence.next_licence, "basic")

        r = self.c.get(reverse("company_accounts:pay_licence", args=(self.company.id,)))
        self.assertContains(r, "Pagar Licencia")
        self.assertContains(r, "Usted ha seleccionado el plan <strong>Basic</strong>")
        self.assertContains(r, "El coste de su licencia es $29 por mes (IVA incluído)")
        # Payment methods
        self.assertContains(r, u"Western Union")
        self.assertContains(r, u"Pague usando Western Union.")
        self.assertContains(r, u"Para ello, envíe $29 en cualquier oficina de Western Union a")
        self.assertContains(r, u"Javier Casas")
        self.assertContains(r, u"Cuando lo haya enviado, introduzca los detalles en el siguiente formulario")
        self.assertContains(r, u"Emitiremos su factura en cuanto comprobemos el pago de su licencia")
        self.assertContains(r, u"Nombres y Apellidos")
        self.assertContains(r, u"Código de Transferencia (MTCN)")
        self.assertContains(r, u"Confirmar Pago")

        with self.new_item(models.LicenceUpdateRequest) as update_request:
            r = self.simulate_post(
                reverse('company_accounts:pay_licence', args=(self.company.id,)),
                {'sender_name': 'Paco Pil',
                 'sender_code': '234567'},
                form_index=0
            )
        self.assertRedirects(r, reverse("company_accounts:company_profile", args=(self.company.id,)))
        self.assertEquals(update_request.licence, self.company.licence)
        today = date.today()
        self.assertEquals(update_request.date, today)
        self.assertEquals(update_request.result, "")
        action = json.loads(update_request.action)
        self.assertEquals(action['new_licence'], "basic")
        self.assertEquals(action['payment_method'], "western_union")
        self.assertEquals(action['sender_name'], "Paco Pil")
        self.assertEquals(action['sender_code'], "234567")
        licence = models.Licence.objects.get(id=self.company.licence.id)
        self.assertEquals(licence.expiration, today + timedelta(days=30))
