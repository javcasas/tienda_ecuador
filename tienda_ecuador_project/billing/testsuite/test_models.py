from django.test import TestCase
from datetime import datetime
import pytz
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
                            Iva, Ice,
                            BillCustomer)
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
                     try_delete,
                     TestHelpersMixin)

from itertools import count

current_ruc = count(10)
get_ruc = lambda: str(current_ruc.next())


def get_date():
    return datetime.now(tz=pytz.timezone('America/Guayaquil'))

base_data = {
    "Company": {
        "nombre_comercial": "Tienda 1",
        "ruc": '1234567890001',
        "razon_social": "Paco Pil",
        "direccion_matriz": "C del pepino",
        "contribuyente_especial": "",
    },
    "BaseCustomer": {
        "razon_social": "Pepe",
        "tipo_identificacion": "ruc",
        "identificacion": "fberg",
        "email": "papa@ble.com",
        "direccion": "dfdf gfwergwer",
    },
    "BaseItem": {
        'sku': 'T123',
        'name': 'Widget',
        'description': 'Widget description',
        'unit_cost': 11.5,
        'unit_price': 15.5,
    },
    "BaseBill": {
        'number': '3',
        'date': get_date(),
    },
    'Iva': {
        'descripcion': "12%",
        'codigo': '12',
        'porcentaje': 12.0,
    },
    'Ice': {
        'descripcion': "Bebidas gaseosas",
        'grupo': 1,
        'codigo': '3051',
        'porcentaje': 50.0,
    },
}


class FieldsTests(TestCase, TestHelpersMixin):
    """
    Tests that check if a given model has all the required fields
    """
    def setUp(self):
        self.company = add_Company(**base_data['Company'])

        self.user = add_User(username="Paco", password='')

        self.customer = add_Customer(**dict(base_data['BaseCustomer'], company=self.company))
        self.bill_customer = add_BillCustomer(**base_data['BaseCustomer'])

        self.proforma_bill = add_ProformaBill(
            **dict(base_data['BaseBill'],
                   company=self.company,
                   issued_to=self.customer))

        self.bill = add_Bill(
            **dict(base_data['BaseBill'],
                   company=self.company,
                   issued_to=self.bill_customer))

        self.iva = add_instance(Iva, **dict(base_data['Iva']))
        self.ice = add_instance(Ice, **dict(base_data['Ice']))

        self.tests = [
            (Company, base_data['Company'],
                {"razon_social": "Pepe Pil",
                 "ruc": "3333333333",
                 "nombre_comercial": "453534"}),
            (CompanyUser, {},
                {'company': self.company,
                 'user': self.user}),
            (Customer, base_data['BaseCustomer'],
                {"company": self.company}),
            (BillCustomer, base_data['BaseCustomer'],
                {}),
            (ProformaBill, base_data['BaseBill'],
                {'company': self.company,
                 'issued_to': self.customer}),
            (Bill, base_data['BaseBill'],
                {'company': self.company,
                 'issued_to': self.bill_customer}),
            (Item, base_data['BaseItem'],
                {"company": self.company,
                 'iva': self.iva,
                 'ice': self.ice,}),
            (ProformaBillItem, base_data['BaseItem'],
                {"proforma_bill": self.proforma_bill,
                 'iva': self.iva,
                 'ice': self.ice,
                 'qty': 6}),
            (BillItem, base_data['BaseItem'],
                {"bill": self.bill,
                 'iva': self.iva,
                 'ice': self.ice,
                 'qty': 8}),
        ]

    def test_all_clases(self):
        for cls, data, updates in self.tests:
            mydata = data.copy()
            mydata.update(updates)
            self.assertHasAllTheRequiredFields(cls, mydata)

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
        self.company = Company.objects.get_or_create(**base_data['Company'])[0]
        self.bill_customer = BillCustomer.objects.get_or_create(**base_data['BaseCustomer'])[0]
        self.iva = Iva(**base_data['Iva'])
        self.iva.save()
        self.ice = Ice(**base_data['Ice'])
        self.ice.save()
        self.tests = [
            (BillCustomer, base_data['BaseCustomer']),
            (Bill,
                {'company': self.company,
                 'number': '3',
                 'date': get_date(),
                 'issued_to': self.bill_customer}),
            (BillItem,
                {'sku': 'T123',
                 'name': 'Widget',
                 'description': 'Widget description',
                 'qty': 14,
                 'unit_cost': 11.5,
                 'unit_price': 15.5,
                 'iva': self.iva,
                 'ice': self.ice,
                 'bill': add_Bill(company=self.company,
                                  number='32',
                                  date=get_date(),
                                  issued_to=self.bill_customer),
                }),
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
        self.company = add_Company(
            nombre_comercial="Tienda 1", ruc='1234567890001',
            razon_social="Paco Pil", direccion_matriz="C del pepino",
            contribuyente_especial="")
        self.user = add_User(username="Paco", password='')

    def test_Customer_to_BillCustomer(self):
        customer = Customer(
            razon_social="Pepe", tipo_identificacion="ruc",
            identificacion="fberg", email="papa@ble.com",
            direccion="dfdf gfwergwer", company=self.company)
        customer.save()
        billcustomer = BillCustomer.fromCustomer(customer)
        self.assertEquals(billcustomer.razon_social, 'Pepe')

    def test_ProformaBill_to_Bill(self):
        proforma = ProformaBill(
            issued_to=Customer.objects.get_or_create(**dict(base_data['BaseCustomer'], company=self.company))[0],
            company=self.company,
            date=get_date(),
            number='3')
        proforma.save()
        bill = Bill.fromProformaBill(proforma)
        self.assertEquals(bill.company, self.company)
        self.assertEquals(bill.number, '3')
        self.assertEquals(bill.issued_to.razon_social, base_data['BaseCustomer']['razon_social'])

    def test_ProformaBillItem_to_BillItem(self):
        proforma = ProformaBill(
            issued_to=Customer.objects.get_or_create(**dict(base_data['BaseCustomer'], company=self.company))[0],
            company=self.company,
            date=get_date(),
            number='3')
        proforma.save()
        iva = Iva(**base_data['Iva'])
        iva.save()
        ice = Ice(**base_data['Ice'])
        ice.save()
        data = dict(sku='T123',
                    name='Widget',
                    description='Widget description',
                    unit_cost=10.5,
                    unit_price=14.5,
                    iva=iva,
                    ice=ice,
                    qty=14)
        proforma_item = ProformaBillItem(proforma_bill=proforma, **data)
        proforma_item.save()
        bill = Bill.fromProformaBill(proforma)
        self.assertObjectMatchesData(bill.items[0], dict(data, bill=bill))
