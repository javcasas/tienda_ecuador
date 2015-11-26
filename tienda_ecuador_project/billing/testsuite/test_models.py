from datetime import datetime, date, timedelta
from itertools import count
from decimal import Decimal
import pytz

from django.test import TestCase
from django.core.exceptions import ValidationError

from billing.models import (Bill,
                            Item,
                            BillItem,
                            Customer,
                            Iva, Ice,
                            ClaveAcceso)

from company_accounts.models import (
                            Company,
                            CompanyUser,
                            Establecimiento,
                            PuntoEmision,
                            )

from billing import models

from helpers import (add_instance,
                     add_User,
                     TestHelpersMixin)


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
        'siguiente_numero_proforma': 4,
        'cert': '',
        'key': '',
    },
    "Establecimiento": {
        "codigo": "001",
        "direccion": "C del pepino",
        "descripcion": "Madre",
    },
    "PuntoEmision": {
        "codigo": "001",
        "descripcion": "Caja principal",
        'siguiente_secuencial_pruebas': 1,
        'siguiente_secuencial_produccion': 1,
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
        'tipo': 'producto',
        'decimales_qty': 0,
    },
    "Bill": {
        'number': '33344556677',
        'date': get_date(),
        'xml_content': '',
        'ride_content': '',
        'fecha_autorizacion': date(2015, 5, 1),
        'numero_autorizacion': '12342423423',
        'ambiente_sri': 'pruebas',
    },
    'Iva': {
        'descripcion': "12%",
        'codigo': '12',
        'porcentaje': 12.0,
    },
    'Ice': {
        'descripcion': "Bebidas gaseosas",
        'codigo': '3051',
        'porcentaje': 50.0,
    },
    'FormaPago': {
        'codigo': '01',
        'descripcion': 'efectivo',
    },
    'PlazoPago': {
        'unidad_tiempo': 'dias',
        'tiempo': 30,
        'descripcion': '30 dias',
    },
    'Pago': {
        'porcentaje': 100,
    },
}


class BaseInstancesMixin(object):
    """
    Some basic instances to help other tests
    """
    def setUp(self):
        super(BaseInstancesMixin, self).setUp()
        self.company = add_instance(Company, **base_data['Company'])

        self.establecimiento = add_instance(Establecimiento,
                                            company=self.company,
                                            **base_data['Establecimiento'])

        self.punto_emision = add_instance(PuntoEmision,
                                          establecimiento=self.establecimiento,
                                          **base_data['PuntoEmision'])

        self.user = add_User(username="Paco", password='')

        self.customer = add_instance(Customer,
            **dict(base_data['BaseCustomer'], company=self.company))

        self.bill = add_instance(
            models.Bill,
            company=self.company,
            **base_data['Bill'])

        self.iva = add_instance(Iva, **dict(base_data['Iva']))
        self.ice = add_instance(Ice, **dict(base_data['Ice']))
        self.forma_pago = add_instance(
            models.FormaPago, **base_data['FormaPago'])
        self.plazo_pago = add_instance(
            models.PlazoPago, **base_data['PlazoPago'])


class FieldsTest(BaseInstancesMixin, TestCase, TestHelpersMixin):
    """
    Tests that check if a given model has all the required fields
    """
    def setUp(self):
        super(FieldsTest, self).setUp()

        self.tests = [
            (Company, base_data['Company'],
                {"razon_social": "Pepe Pil",
                 "ruc": "3333333333",
                 "nombre_comercial": "453534"}),
            (CompanyUser, {},
                {'company': self.company,
                 'user': self.user}),
            (Establecimiento, base_data['Establecimiento'],
                {'company': self.company}),
            (PuntoEmision, base_data['PuntoEmision'],
                {'establecimiento': self.establecimiento}),
            (Customer, base_data['BaseCustomer'],
                {"company": self.company}),
            (Bill, base_data['Bill'],
                {'company': self.company,
                 'fecha_autorizacion': datetime(2015, 5, 1, tzinfo=pytz.timezone('America/Guayaquil')),
                 'numero_autorizacion': '12342423423',
                 'ambiente_sri': 'pruebas'}),
            (Item, base_data['BaseItem'],
                {"company": self.company,
                 }),
            (BillItem, base_data['BaseItem'],
                {"bill": self.bill,
                 'qty': 6}),
            (models.FormaPago, base_data['FormaPago'],
                {}),
            (models.PlazoPago, base_data['PlazoPago'],
                {}),
            (models.Pago, base_data['Pago'],
                {'forma_pago': self.forma_pago,
                 'plazo_pago': self.plazo_pago,
                 'bill': self.bill}),
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
            ob.full_clean()
        except ValidationError as e:
            self.fail("Error testing {}: {}".format(cls, e))
        try:
            save = ob.secret_save
        except AttributeError:
            save = ob.save
        save()
        msg = str(cls)
        self.assertObjectMatchesData(cls.objects.get(id=ob.id), data, msg)


class UnicodeTests(TestCase, TestHelpersMixin):
    def test_forma_pago(self):
        data = base_data['FormaPago']
        ob = models.FormaPago(**data)
        self.assertEquals(
            unicode(ob),
            data['descripcion'])

    def test_plazo_pago(self):
        data = base_data['PlazoPago']
        ob = models.PlazoPago(**data)
        self.assertEquals(
            unicode(ob),
            u'{} ({} {})'.format(data['descripcion'],
                                 data['tiempo'],
                                 data['unidad_tiempo']))


class CompanyUserTests(TestCase, TestHelpersMixin):
    def setUp(self):
        self.company = add_instance(Company, **base_data['Company'])
        self.user = add_User(username="Paco", password='')
        self.company_user = add_instance(CompanyUser,
                                         company=self.company,
                                         user=self.user)

    def test_unicode(self):
        self.assertEquals(str(self.company_user),
                          self.company_user.user.username)


class ItemTests(BaseInstancesMixin, TestCase, TestHelpersMixin):
    """
    Tests for the Item classes
    """
    def test_total_sin_impuestos(self):
        """
        Prueba el atributo "total_sin_impuestos"
        que devuelve el total correspondiente a un item
        sin contar los impuestos
        """
        item = BillItem(sku="1234", name="asdf", description="asdf",
                        unit_cost=10, unit_price=14, qty=6)
        self.assertEquals(item.total_sin_impuestos, 6 * 14)

    def test_bill_item_iva_ice(self):
        """
        Prueba los calculos de iva e ice
        """
        item = BillItem(
            sku="1234", name="asdf", description="asdf", unit_cost=10,
            unit_price=10, qty=6, bill=self.bill)
        item.save()
        item.tax_items.add(self.iva, self.ice)

        # ICE
        self.assertEquals(item.base_imponible_ice,
                          item.total_sin_impuestos)
        valor_ice = item.base_imponible_ice * Decimal("0.5")
        self.assertEquals(item.valor_ice, valor_ice)

        # IVA
        self.assertEquals(item.base_imponible_iva,
                          item.total_sin_impuestos + valor_ice)
        valor_iva = item.base_imponible_iva * Decimal("0.12")
        self.assertEquals(item.valor_iva, valor_iva)
        self.assertEquals(item.total_impuestos, valor_iva + valor_ice)

    def test_unicode(self):
        """
        Prueba str() y unicode()
        """
        ob = Item(sku="1234", name="asdf", description="asdf",
                  unit_cost=10, unit_price=10)
        self.assertEquals(str(ob), "1234 - asdf")

    def test_increment(self):
        """
        """
        ob = Item(sku="1234", name="asdf", description="asdf",
                  unit_cost=10, unit_price=10, decimales_qty=2)
        self.assertEquals(ob.increment_qty, "0.01")

    def test_increment_no_decimals(self):
        """
        """
        ob = BillItem(sku="1234", name="asdf", description="asdf",
                      unit_cost=10, unit_price=10, decimales_qty=0)
        self.assertEquals(ob.increment_qty, "1")


class IdentificacionTests(TestCase):
    def setUp(self):
        self.company = add_instance(Company,
            nombre_comercial="Tienda 1", ruc='1234567890001',
            razon_social="Paco Pil", direccion_matriz="C del pepino",
            contribuyente_especial="")

    def valid(self, tipo_identificacion, identificacion):
        """
        tests a valid identification
        """
        Customer(razon_social="Paco Pil",
                 tipo_identificacion=tipo_identificacion,
                 identificacion=identificacion,
                 company=self.company).save()

    def invalid(self, tipo_identificacion, identificacion):
        """
        tests an invalid identification
        """
        with self.assertRaises(ValidationError):
            self.valid(tipo_identificacion=tipo_identificacion,
                       identificacion=identificacion)

    def test_valid_ruc(self):
        """
        A valid RUC
        """
        self.valid(tipo_identificacion="ruc",
                   identificacion="1756760292001")

    def test_valid_ruc_consumidor_final(self):
        """
        consumidor_final
        """
        self.valid(tipo_identificacion="ruc",
                   identificacion="9999999999999")

    def test_invalid_ruc_does_not_end_001(self):
        """
        An invalid RUC that does not end in 001
        """
        self.invalid(tipo_identificacion="ruc",
                     identificacion="1756760292002")

    def test_invalid_ruc_not_13_digits(self):
        """
        An invalid RUC that is not 13 digits
        """
        self.invalid(tipo_identificacion="ruc",
                     identificacion="175676029201")

    def test_invalid_ruc_bad_verifier(self):
        """
        An invalid RUC that has a bad verifier digit
        """
        self.invalid(tipo_identificacion="ruc",
                     identificacion="1756760293001")

    def test_unknown_identification_type(self):
        """
        An unknown identificacion
        """
        self.invalid(tipo_identificacion="patata",
                     identificacion="173831152001")

    def test_valid_cedula(self):
        """
        A valid cedula
        """
        self.valid(tipo_identificacion="cedula",
                   identificacion="1756760292")

    def test_invalid_cedula_invalid_length(self):
        """
        An invalid cedula with the wrong number of digits
        """
        self.invalid(tipo_identificacion="cedula",
                     identificacion="1738331533")

    def test_invalid_cedula_bad_verifier(self):
        """
        An invalid cedula with a bad verifier digit
        """
        self.invalid(tipo_identificacion="cedula",
                     identificacion="173831153")


class BillTest(TestCase, TestHelpersMixin):
    """
    Test that checks that a final model can be created,
    but not modified
    """
    def setUp(self):
        self.company = Company.objects.get_or_create(**base_data['Company'])[0]
        self.establecimiento = add_instance(Establecimiento,
                                            company=self.company,
                                            **base_data['Establecimiento'])
        self.punto_emision = add_instance(PuntoEmision,
                                          establecimiento=self.establecimiento,
                                          **base_data['PuntoEmision'])
        self.customer = Customer.objects.get_or_create(
            company=self.company, **base_data['BaseCustomer'])[0]
        self.iva = add_instance(Iva, **base_data['Iva'])
        self.ice = add_instance(Ice, **base_data['Ice'])
        self.bill = add_instance(Bill,
                                 punto_emision=self.punto_emision,
                                 number='3',
                                 date=get_date(),
                                 company=self.company,
                                 issued_to=self.customer)
        for i in range(1, 5):
            ob = add_instance(BillItem,
                              bill=self.bill,
                              sku='T123{}'.format(i),
                              name='Widget{}'.format(i),
                              description='Widget description',
                              qty=i,
                              unit_cost=5,
                              unit_price=10,)
            ob.tax_items.add(self.iva, self.ice)
        self.payment = add_instance(
            models.Pago,
            porcentaje=Decimal(100),
            bill=self.bill,
            forma_pago=add_instance(
                models.FormaPago,
                codigo='01',
                descripcion='Efectivo'),
            plazo_pago=add_instance(
                models.PlazoPago,
                descripcion='30 dias',
                unidad_tiempo='dias',
                tiempo=30))

    def test_subtotal(self):
        self.assertEquals(self.bill.subtotal,
                          {12: (1 + 2 + 3 + 4) * (10 + 5),
                           0: 0})
        for k, v in self.bill.subtotal.iteritems():
            self.assertEquals(type(v), Decimal)

    def test_total_sin_impuestos(self):
        self.assertEquals(self.bill.total_sin_impuestos,
                          (1 + 2 + 3 + 4) * 10)
        self.assertEquals(type(self.bill.total_sin_impuestos), Decimal)

    def test_total_con_impuestos(self):
        self.assertEquals(self.bill.total_con_impuestos,
                          (1 + 2 + 3 + 4) * (10 + 5) * Decimal("1.12"))
        self.assertEquals(type(self.bill.total_con_impuestos), Decimal)

    def test_impuestos(self):
        expected = [
            {
                "codigo": "2",
                "codigo_porcentaje": base_data['Iva']['codigo'],
                "porcentaje": base_data['Iva']['porcentaje'],
                "base_imponible": Decimal((1 + 2 + 3 + 4) * (10 + 5)),
                'valor': (1 + 2 + 3 + 4) * (10 + 5) * Decimal("0.12"),
            },
            {
                "codigo": "3",
                "codigo_porcentaje": base_data['Ice']['codigo'],
                "porcentaje": base_data['Ice']['porcentaje'],
                "base_imponible": Decimal((1 + 2 + 3 + 4) * 10),
                'valor': (1 + 2 + 3 + 4) * 10 * Decimal("0.5"),
            },
        ]
        self.assertEquals(self.bill.impuestos, expected)

    def test_iva(self):
        unidades = 1 + 2 + 3 + 4
        precio_unitario = 10
        factor_ice = 1.5
        factor_iva = 0.12
        total = (unidades * precio_unitario) * factor_ice * factor_iva
        self.assertEquals(
            self.bill.iva,
            {
                Decimal(0): Decimal(0),
                Decimal(12): Decimal(total),
            })
        self.assertEquals(type(self.bill.iva[0]), Decimal)
        self.assertEquals(type(self.bill.iva[12]), Decimal)

    def test_clave_acceso_encode(self):
        c = ClaveAcceso()
        c.fecha_emision = (2015, 7, 3)
        c.tipo_comprobante = "factura"
        c.ruc = "1790746119001"
        c.ambiente = "produccion"
        c.establecimiento = 23
        c.punto_emision = 13
        c.numero = 174
        c.codigo = 17907461
        c.tipo_emision = "normal"
        expected = ("03072015" "01" "1790746119001" "2"
                    "023013" "000000174" "17907461" "1" "1")
        self.assertEquals(unicode(c), expected)

        c.codigo = 17907462
        expected = ("03072015" "01" "1790746119001" "2"
                    "023013" "000000174" "17907462" "1" "7")
        self.assertEquals(unicode(c), expected)

        c.codigo = 17907468
        expected = ("03072015" "01" "1790746119001" "2"
                    "023013" "000000174" "17907468" "1" "0")
        self.assertEquals(unicode(c), expected)

    def test_clave_acceso_invalid_fecha_emision(self):
        c = ClaveAcceso()
        with self.assertRaises(ValueError):
            c.fecha_emision = (2015, 17, 3)

    def test_attached_payments(self):
        self.assertEquals(list(self.bill.payment),
                          [self.payment])

    def test_payment_qty(self):
        self.assertEquals(self.bill.payment[0].cantidad,
                          self.bill.total_con_impuestos)

    def test_proforma_to_send_field_checks(self):
        """
        Una proforma para ser enviada al SRI debe tener
            clave de acceso
            XML
            punto de emision
            Pasa a ser no editable
        """
        bill = self.bill

        def get_bill_from_db():
            return models.Bill.objects.get(id=bill.id)

        self.assertEquals(bill.status, 'proforma')
        data = {
            'clave_acceso':  ('1234512345', ''),
            'xml_content':      ('<xml></xml>', ''),
            'punto_emision': (self.punto_emision, None),
        }
        for key in data.keys():
            bill.status = 'proforma'
            to_test = data.copy()
            to_test.pop(key)
            for nonempty_key, value in to_test.iteritems():
                setattr(bill, nonempty_key, value[0])
            setattr(bill, key, data[key][1])
            bill.status = 'a enviar'
            with self.assertRaises(ValidationError):  # Save everything with the status change
                bill.save()
            self.assertEquals(get_bill_from_db().status, 'proforma')

            bill.status = 'proforma'  # Save everything, then the status change
            bill.save()
            bill.status = 'a enviar'
            with self.assertRaises(ValidationError):
                bill.save()
            self.assertEquals(get_bill_from_db().status, 'proforma')

        # Success
        for key, value in data.iteritems():
            setattr(bill, key, value[0])
        bill.status = 'a enviar'
        bill.save()
        self.assertEquals(get_bill_from_db().status, 'a enviar')

        # Test non-writable
        bill.xml_data = 'No data'
        with self.assertRaises(ValidationError):
            bill.save()
        self.assertEquals(get_bill_from_db().xml_content, data['xml_content'][0])

    def test_cant_modify_bill_not_proforma(self):
        """
        No se puede modificar una factura que no este en status='proforma'
        """
        bill = self.bill

        def get_bill_from_db():
            return models.Bill.objects.get(id=bill.id)

        self.assertEquals(bill.status, 'proforma')
        bill.clave_acceso = '1234512345'
        bill.xml_content = '<xml></xml>'
        bill.punto_emision = self.punto_emision
        bill.status = 'a enviar'
        bill.save()

        with self.assertRaises(ValidationError):
            bill.clave_acceso = '333333'
            bill.save()

        with self.assertRaises(ValidationError):
            item = bill.items[0]
            item.qty = 4
            item.save()

        with self.assertRaises(ValidationError):
            bill.items[0].delete()

        with self.assertRaises(ValidationError):
            payment = bill.payment[0]
            payment.porcentaje = 4
            payment.save()

        with self.assertRaises(ValidationError):
            bill.payment[0].delete()



class IceTests(TestCase, TestHelpersMixin):
    def setUp(self):
        self.ice = add_instance(Ice,
                                descripcion="Gaseosas",
                                codigo="asdf",
                                porcentaje=50)

    def test_nonzero(self):
        self.assertTrue(self.ice)
        self.assertFalse(
            add_instance(Ice,
                         descripcion="No ICE",
                         codigo="", porcentaje=0))
