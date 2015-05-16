from django.test import TestCase
from unittest import skip
from billing.models import (ReadOnlyObject,
                            Company,
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
                 'qty': 14,
                 'proforma_bill': add_ProformaBill(company=self.company,
                                                   number='3',
                                                   issued_to=add_ProformaBillCustomer(name='Pepe'))}),
            (BillItem,
                {'sku': 'T123',
                 'name': 'Widget',
                 'description': 'Widget description',
                 'qty': 14,
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
                 'qty': 14,
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
            with self.assertRaises(ReadOnlyObject):
                ob.save()
            with self.assertRaises(ReadOnlyObject):
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


class ProformaToFinalTests(TestCase, TestHelpersMixin):
    """
    Tests that check converting a proforma into a final
    """
    def setUp(self):
        self.company = add_Company(name="Tienda 1")
        self.user = add_User(username="Paco", password='')
        self.tests = [
            (ProformaBillCustomer,
                {'name': "Pepe"}),
            (BillCustomer,
                {'name': "Pepe"}),
            (ProformaBill,
                {'company': self.company,
                 'number': '3',
                 'issued_to': add_ProformaBillCustomer(name='Pepe')}),
            (Bill,
                {'company': self.company,
                 'number': '3',
                 'issued_to': add_BillCustomer(name='Pepe')}),
            (ProformaBillItem,
                {'sku': 'T123',
                 'name': 'Widget',
                 'description': 'Widget description',
                 'qty': 14,
                 'proforma_bill': add_ProformaBill(company=self.company,
                                                   number='3',
                                                   issued_to=add_ProformaBillCustomer(name='Pepe'))}),
            (BillItem,
                {'sku': 'T123',
                 'name': 'Widget',
                 'description': 'Widget description',
                 'qty': 14,
                 'bill': add_Bill(company=self.company,
                                  number='32',
                                  issued_to=add_BillCustomer(name='Pepe'))}),
        ]

    def test_ProformaBillCustomer_to_BillCustomer(self):
        proforma = ProformaBillCustomer(name="Pepe")
        proforma.save()
        billcustomer = proforma.toBillCustomer()
        self.assertEquals(billcustomer.name, 'Pepe')

    def test_ProformaBill_to_Bill(self):
        proforma = ProformaBill(issued_to=add_ProformaBillCustomer(name='Pepe'),
                                company=self.company,
                                number='3')
        proforma.save()
        bill = proforma.toBill()
        self.assertEquals(bill.company, self.company)
        self.assertEquals(bill.number, '3')
        self.assertEquals(bill.issued_to.name, 'Pepe')

    def test_ProformaBillItem_to_BillItem(self):
        proforma = ProformaBill(issued_to=add_ProformaBillCustomer(name='Pepe'),
                                company=self.company,
                                number='3')
        proforma.save()
        bill = proforma.toBill()
        data = dict(sku='T123',
                    name='Widget',
                    description='Widget description',
                    qty=14)
        proforma_item = ProformaBillItem(proforma_bill=proforma, **data)
        proforma_item.save()
        item = proforma_item.toBillItem(bill)
        self.assertObjectMatchesData(item, dict(data, bill=bill))
