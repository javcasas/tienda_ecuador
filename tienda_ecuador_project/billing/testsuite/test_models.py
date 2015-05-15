from django.test import TestCase
from unittest import skip
from billing.models import (Company,
                            CompanyUser,
                            ProformaBill,
                            Bill,
                            Item,
                            ProformaBillItem,
                            BillItem,
                            Customer,
                            BillCustomer,
                            ProformaBillCustomer)
from django.contrib.auth.models import User
from helpers import (add_instance,
                     add_User,
                     add_Company,
                     add_CompanyUser,
                     add_ProformaBill,
                     add_Bill,
                     add_Item,
                     add_ProformaBillItem,
                     add_BillItem,
                     add_Customer,
                     add_BillCustomer,
                     add_ProformaBillCustomer,
                     try_delete,
                     TestHelpersMixin)


class FieldsTests(TestCase, TestHelpersMixin):
    """
    Tests that check if a given model has all the required fields
    """
    def setUp(self):
        self.company = add_Company(name="Tienda 1")
        self.user = add_User(username="Paco", password='')
        self.tests = [
            (Company,
                {'name': 'Tienda 2',
                 'sri_ruc': '1234567890',
                 'sri_razon_social': 'ABC DEF'}),
            (CompanyUser,
                {'company': self.company,
                 'user': self.user}),
            (Customer,
                {'name': "Pepe",
                 'company': self.company}),
            (BillCustomer,
                {'name': "Pepe"}),
            (ProformaBillCustomer,
                {'name': "Pepe"}),
            (ProformaBill,
                {'company': self.company,
                 'number': '3',
                 'issued_to': add_ProformaBillCustomer(name='Pepe')}),
            (Bill,
                {'company': self.company,
                 'number': '3',
                 'issued_to': add_BillCustomer(name='Pepe')}),
            (Item,
                {'sku': 'T123',
                 'name': 'Widget',
                 'description': 'Widget description',
                 'company': self.company}),
            (ProformaBillItem,
                {'sku': 'T123',
                 'name': 'Widget',
                 'description': 'Widget description',
                 'proforma_bill': add_ProformaBill(company=self.company,
                                                   number='3',
                                                   issued_to=add_ProformaBillCustomer(name='Pepe'))}),
            (BillItem,
                {'sku': 'T123',
                 'name': 'Widget',
                 'description': 'Widget description',
                 'bill': add_Bill(company=self.company,
                                  number='32',
                                  issued_to=add_BillCustomer(name='Pepe'))}),
        ]

    def test_all_clases(self):
        for cls, data in self.tests:
            self.assertHasAllTheRequiredFields(cls, data)

    def assertHasAllTheRequiredFields(self, cls, data):
        """
        Actually tests if all the required fields are there
        """
        ob = cls(**data)
        try:
            save = ob.secret_save
        except AttributeError:
            save = ob.save
        save()
        msg = str(cls)
        self.assertObjectMatchesData(cls.objects.get(id=ob.id), data, msg)


class ReadOnlyTests(TestCase, TestHelpersMixin):
    """
    Test that checks that a final model can be created,
    but not modified
    """
    def setUp(self):
        self.company = add_Company(name="Tienda 1")
        self.tests = [
            (BillCustomer,
                {'name': "Pepe"}),
            (Bill,
                {'company': self.company,
                 'number': '3',
                 'issued_to': add_BillCustomer(name='Pepe')}),
            (BillItem,
                {'sku': 'T123',
                 'name': 'Widget',
                 'description': 'Widget description',
                 'bill': add_Bill(company=self.company,
                                  number='32',
                                  issued_to=add_BillCustomer(name='Pepe'))}),
        ]

    def test_update_disabled(self):
        '''
        Ensures save and delete fails for read only classes
        '''
        for cls, data in self.tests:
            ob = cls(**data)
            ob.save()
            with self.assertRaises(Exception):
                ob.save()
            with self.assertRaises(Exception):
                ob.delete()

    def test_secret_methods(self):
        '''
        Ensures secret_save and secret_delete works
        '''
        for cls, data in self.tests:
            ob = cls(**data)
            ob.save()
            ob.secret_save()
            ob.secret_delete()
            with self.assertRaises(cls.DoesNotExist):
                cls.objects.get(id=ob.id)
