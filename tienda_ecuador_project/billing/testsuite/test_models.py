from django.test import TestCase
from datetime import datetime
import pytz
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
                            BillItemIva, BillItemIce,
                            ItemInBill,
                            BillCustomer)
from helpers import (add_instance,
                     add_User,
                     add_Company,
                     add_ProformaBill,
                     add_Bill,
                     add_Customer,
                     add_BillCustomer,
                     TestHelpersMixin)

from itertools import count
from decimal import Decimal
from django.core.exceptions import ValidationError

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
        "identificacion": "1713831152001",
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

        self.customer = add_Customer(
            **dict(base_data['BaseCustomer'], company=self.company))
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

        self.bill_iva = add_instance(BillItemIva, **dict(base_data['Iva']))
        self.bill_ice = add_instance(BillItemIce, **dict(base_data['Ice']))

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
                 'ice': self.ice}),
            (ProformaBillItem, base_data['BaseItem'],
                {"proforma_bill": self.proforma_bill,
                 'iva': self.iva,
                 'ice': self.ice,
                 'qty': 6}),
            (BillItem, base_data['BaseItem'],
                {"bill": self.bill,
                 'iva': self.bill_iva,
                 'ice': self.bill_ice,
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
        self.bill_customer = BillCustomer.objects.get_or_create(
            **base_data['BaseCustomer'])[0]
        self.iva = add_instance(Iva, **base_data['Iva'])
        self.ice = add_instance(Ice, **base_data['Ice'])
        self.bill_iva = add_instance(BillItemIva, **base_data['Iva'])
        self.bill_ice = add_instance(BillItemIce, **base_data['Ice'])
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
                 'iva': self.bill_iva,
                 'ice': self.bill_ice,
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
            identificacion="1713831152001", email="papa@ble.com",
            direccion="dfdf gfwergwer", company=self.company)
        customer.save()
        billcustomer = BillCustomer.fromCustomer(customer)
        self.assertEquals(billcustomer.razon_social, 'Pepe')

    def test_ProformaBill_to_Bill(self):
        proforma = ProformaBill(
            issued_to=Customer.objects.get_or_create(
                **dict(base_data['BaseCustomer'], company=self.company))[0],
            company=self.company,
            date=get_date(),
            number='3')
        proforma.save()
        bill = Bill.fromProformaBill(proforma)
        self.assertEquals(bill.company, self.company)
        self.assertEquals(bill.number, '3')
        self.assertEquals(bill.issued_to.razon_social,
                          base_data['BaseCustomer']['razon_social'])

    def test_ProformaBillItem_to_BillItem(self):
        proforma = ProformaBill(
            issued_to=Customer.objects.get_or_create(
                **dict(base_data['BaseCustomer'], company=self.company))[0],
            company=self.company,
            date=get_date(),
            number='3')
        proforma.save()
        iva = add_instance(Iva, **base_data['Iva'])
        ice = add_instance(Ice, **base_data['Ice'])
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
        self.assertObjectMatchesData(
            bill.items[0],
            dict(data, bill=bill,
                 iva=BillItemIva.fromIva(iva),
                 ice=BillItemIce.fromIce(ice)))


class ItemTests(TestCase, TestHelpersMixin):
    """
    Tests for the Item classes
    """
    def test_subtotal(self):
        ob = ItemInBill(sku="1234", name="asdf", description="asdf",
                        unit_cost=10, unit_price=14, qty=6)
        self.assertEquals(ob.subtotal, 6 * 14)

    def test_bill_item_iva_ice(self):
        iva = Iva(descripcion="12%", codigo="12", porcentaje=12)
        ice = Ice(descripcion="Gaseosas", codigo="145", grupo=1, porcentaje=50)
        ob = ProformaBillItem(sku="1234", name="asdf", description="asdf",
                              unit_cost=10, unit_price=10, qty=6,
                              iva=iva, ice=ice)
        valor_ice = ob.subtotal * Decimal("0.5")
        self.assertEquals(ob.valor_ice, valor_ice)
        valor_iva = (ob.subtotal + valor_ice) * Decimal("0.12")
        self.assertEquals(ob.valor_iva, valor_iva)
        self.assertEquals(ob.total_impuestos, valor_iva + valor_ice)


class IdentificacionTests(TestCase):
    def setUp(self):
        self.company = add_Company(
            nombre_comercial="Tienda 1", ruc='1234567890001',
            razon_social="Paco Pil", direccion_matriz="C del pepino",
            contribuyente_especial="")

    def valid(self, tipo_identificacion, identificacion):
        c = Customer(razon_social="Paco Pil",
                     tipo_identificacion=tipo_identificacion,
                     identificacion=identificacion,
                     company=self.company)
        c.save()

    def invalid(self, tipo_identificacion, identificacion):
        with self.assertRaises(ValidationError):
            self.valid(tipo_identificacion=tipo_identificacion,
                       identificacion=identificacion)

    def test_valid_ruc(self):
        self.valid(tipo_identificacion="ruc",
                   identificacion="1756760292001")

    def test_invalid_ruc_does_not_end_001(self):
        self.invalid(tipo_identificacion="ruc",
                     identificacion="1756760292002")

    def test_invalid_ruc_not_13_digits(self):
        self.invalid(tipo_identificacion="ruc",
                     identificacion="175676029201")

    def test_invalid_ruc_bad_verifier(self):
        self.invalid(tipo_identificacion="ruc",
                     identificacion="1756760293001")
                                     

    def test_unknown_identification_type(self):
        self.invalid(tipo_identificacion="patata",
                     identificacion="173831152001")

    def test_valid_cedula(self):
        self.valid(tipo_identificacion="cedula",
                   identificacion="1756760292")

    def test_invalid_cedula_invalid_length(self):
        self.invalid(tipo_identificacion="cedula",
                     identificacion="1738331533")

    def test_invalid_cedula_bad_verifier(self):
        self.invalid(tipo_identificacion="cedula",
                     identificacion="173831153")


class ProformaBillTest(TestCase, TestHelpersMixin):
    """
    Test that checks that a final model can be created,
    but not modified
    """
    def setUp(self):
        self.company = Company.objects.get_or_create(**base_data['Company'])[0]
        self.customer = Customer.objects.get_or_create(
            company=self.company, **base_data['BaseCustomer'])[0]
        self.iva = add_instance(Iva, **base_data['Iva'])
        self.ice = add_instance(Ice, **base_data['Ice'])
        self.bill_iva = add_instance(BillItemIva, **base_data['Iva'])
        self.bill_ice = add_instance(BillItemIce, **base_data['Ice'])
        self.proforma = add_instance(ProformaBill,
                                     company=self.company,
                                     number='3',
                                     date=get_date(),
                                     issued_to=self.customer)
        for i in range(1, 5):
            add_instance(ProformaBillItem,
                         proforma_bill=self.proforma,
                         sku='T123{}'.format(i),
                         name='Widget{}'.format(i),
                         description='Widget description',
                         qty=i,
                         unit_cost=5,
                         unit_price=10,
                         iva=self.bill_iva,
                         ice=self.bill_ice)

    def test_subtotal(self):
        self.assertEquals(self.proforma.subtotal, (1 + 2 + 3 + 4) * 10)

    def test_iva(self):
        unidades = 1 + 2 + 3 + 4
        precio_unitario = 10
        factor_ice = 1.5
        factor_iva = 0.12
        total = (unidades * precio_unitario) * factor_ice * factor_iva
        self.assertEquals(
            self.proforma.iva, 
            {
                Decimal(12): Decimal(total)
            })
