from datetime import datetime
from itertools import count
from decimal import Decimal
import pytz

from django.test import TestCase
from django.core.exceptions import ValidationError

from sri.models import Iva, Ice
import inventory.testsuite.test_models
from billing.models import (Bill,
                            BillItem,
                            Customer,
                            ClaveAcceso)

from company_accounts.models import (Company,
                                     CompanyUser,
                                     Establecimiento,
                                     PuntoEmision)

from billing import models

from helpers import (add_instance,
                     add_User,
                     TestHelpersMixin)

from sri.models import SRIStatus, AmbienteSRI


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
    "BillItem": {
        'qty': 4,
    },
    "Bill": {
        'number': '33344556677',
        'date': get_date(),
        'xml_content': '',
        'fecha_autorizacion':
            datetime(2015, 5, 1, tzinfo=pytz.timezone('America/Guayaquil')),
        'numero_autorizacion': '12342423423',
        'ambiente_sri': AmbienteSRI.options.pruebas,
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


class MakeBaseInstances(inventory.testsuite.test_models.MakeBaseInstances):
    def setUp(self):
        inventory.testsuite.test_models.MakeBaseInstances.setUp(self)
        self.forma_pago = add_instance(
            models.FormaPago, **base_data['FormaPago'])
        self.plazo_pago = add_instance(
            models.PlazoPago, **base_data['PlazoPago'])
        self.customer = add_instance(
            Customer,
            company=self.company,
            **base_data['BaseCustomer'])
        self.bill = add_instance(
            models.Bill,
            company=self.company,
            issued_to=self.customer,
            punto_emision=self.punto_emision,
            **base_data['Bill'])
        self.bill_item = add_instance(
            BillItem,
            sku=self.sku,
            bill=self.bill,
            qty=6)
        self.pago = add_instance(
            models.Pago,
            porcentaje=Decimal(100),
            bill=self.bill,
            forma_pago=self.forma_pago,
            plazo_pago=self.plazo_pago)


class MakeBaseInstances(MakeBaseInstances):
    """
    Some basic instances to help other tests
    """
    def setUp(self):
        super(MakeBaseInstances, self).setUp()
        self.customer = add_instance(
            Customer,
            company=self.company,
            **base_data['BaseCustomer'])

        self.bill = add_instance(
            models.Bill,
            company=self.company,
            **base_data['Bill'])

        self.forma_pago = add_instance(
            models.FormaPago, **base_data['FormaPago'])
        self.plazo_pago = add_instance(
            models.PlazoPago, **base_data['PlazoPago'])


class FieldsTest(MakeBaseInstances, TestCase, TestHelpersMixin):
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
                 'fecha_autorizacion':
                    datetime(2015, 5, 1,
                             tzinfo=pytz.timezone('America/Guayaquil')),
                 'numero_autorizacion': '12342423423',
                 'ambiente_sri': AmbienteSRI.options.pruebas}),
            (BillItem, base_data['BillItem'],
                {"bill": self.bill,
                 'sku': self.sku,
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


class BillItemTests(MakeBaseInstances, TestCase, TestHelpersMixin):
    """
    Tests for the BillItem classes
    """
    def test_total_sin_impuestos(self):
        """
        Prueba el atributo "total_sin_impuestos"
        que devuelve el total correspondiente a un item
        sin contar los impuestos
        """
        self.assertEquals(self.bill_item.total_sin_impuestos, self.sku.unit_price * self.bill_item.qty)

    def test_bill_item_iva_ice(self):
        """
        Prueba los calculos de iva e ice
        """
        # ICE
        self.assertEquals(self.bill_item.base_imponible_ice,
                          self.bill_item.total_sin_impuestos)
        valor_ice = self.bill_item.base_imponible_ice * Decimal("0.5")
        self.assertEquals(self.bill_item.valor_ice, valor_ice)

        # IVA
        self.assertEquals(self.bill_item.base_imponible_iva,
                          self.bill_item.total_sin_impuestos + valor_ice)
        valor_iva = self.bill_item.base_imponible_iva * Decimal("0.12")
        self.assertEquals(self.bill_item.valor_iva, valor_iva)
        self.assertEquals(self.bill_item.total_impuestos, valor_iva + valor_ice)

    #def test_unicode(self):
    #    """
    #    Prueba str() y unicode()
    #    """
    #    ob = Item(sku="1234", name="asdf", description="asdf",
    #              unit_cost=10, unit_price=10)
    #    self.assertEquals(str(ob), "1234 - asdf")

    def test_increment(self):
        """
        """
        item = self.item
        item.decimales_qty = 2
        item.save()
        self.assertEquals(self.bill_item.increment_qty, "0.01")

    def test_increment_no_decimals(self):
        """
        """
        self.assertEquals(self.bill_item.increment_qty, "1")
    
    def test_name(self):
        self.assertEquals(self.bill_item.name, self.bill_item.sku.batch.item.name)

    def test_code(self):
        self.assertEquals(self.bill_item.code, self.bill_item.sku.code)

    def test_unit_price(self):
        self.assertEquals(self.bill_item.unit_price, self.bill_item.sku.unit_price)


class IdentificacionTests(TestCase):
    def setUp(self):
        self.company = add_instance(
            Company,
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


class BillTest(MakeBaseInstances, TestCase, TestHelpersMixin):
    """
    Test that checks that a final model can be created,
    but not modified
    """
    def get_bill(self):
        return models.Bill.objects.get(id=self.bill.id)

    def test_subtotal(self):
        self.assertEquals(self.bill.subtotal,
                          {12: 6 * 20 * Decimal("1.50"),
                           0: 0})
        for k, v in self.bill.subtotal.iteritems():
            self.assertEquals(type(v), Decimal)

    def test_total_sin_impuestos(self):
        total = sum([item.qty * item.sku.unit_price for item in self.bill.items])
        self.assertEquals(self.bill.total_sin_impuestos,
                          total)
        self.assertEquals(type(self.bill.total_sin_impuestos), Decimal)

    def test_total_con_impuestos(self):
        self.assertEquals(self.bill.total_con_impuestos,
                          6 * 20 * Decimal("1.50") * Decimal("1.12"))
        self.assertEquals(type(self.bill.total_con_impuestos), Decimal)

    def test_impuestos(self):
        expected = [
            {
                "codigo": "2",
                "codigo_porcentaje": base_data['Iva']['codigo'],
                "porcentaje": base_data['Iva']['porcentaje'],
                "base_imponible": 6 * 20 * Decimal("1.50"),
                'valor': 6 * 20 * Decimal("1.50") * Decimal("0.12"),
            },
            {
                "codigo": "3",
                "codigo_porcentaje": base_data['Ice']['codigo'],
                "porcentaje": base_data['Ice']['porcentaje'],
                "base_imponible": 6 * 20,
                'valor': 6 * 20 * Decimal("0.5"),
            },
        ]
        self.assertEquals(self.bill.impuestos, expected)

    def test_iva(self):
        self.assertEquals(
            self.bill.iva,
            {
                Decimal(0): Decimal(0),
                Decimal(12): 6 * 20 * Decimal("1.50") * Decimal("0.12"),
            })
        self.assertEquals(type(self.bill.iva[0]), Decimal)
        self.assertEquals(type(self.bill.iva[12]), Decimal)

    def test_clave_acceso_encode(self):
        c = ClaveAcceso()
        c.fecha_emision = (2015, 7, 3)
        c.tipo_comprobante = "factura"
        c.ruc = "1790746119001"
        c.ambiente = AmbienteSRI.options.produccion
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
                          [self.pago])

    def test_payment_qty(self):
        self.assertEquals(self.bill.payment[0].cantidad,
                          self.bill.total_con_impuestos)

    def test_bill_default_status(self):
        """
        The default status for a bill is 'no enviada'
        """
        bill = self.get_bill()
        self.assertEquals(bill.status, SRIStatus.options.NotSent)

    def test_proforma_to_send_incomplete_fields_checks(self):
        """
        Una proforma para ser enviada al SRI debe tener
            date
            punto_emision
                -> secuencial
                -> ambiente SRI
            datos
            Pasa a ser no editable
        """
        # No date
        bill = self.get_bill()
        bill.date = None
        bill.punto_emision = self.punto_emision
        bill.status = SRIStatus.options.ReadyToSend
        with self.assertRaises(ValidationError):
            bill.save()
        self.assertEquals(self.get_bill().status,
                          SRIStatus.options.NotSent)

        # No punto_emision
        bill = self.get_bill()
        bill.date = get_date()
        bill.punto_emision = None
        bill.status = SRIStatus.options.ReadyToSend
        with self.assertRaises(ValidationError):
            bill.save()
        self.assertEquals(self.get_bill().status,
                          SRIStatus.options.NotSent)

    def test_proforma_to_send_complete_fields_checks(self):
        """
        Una proforma para ser enviada al SRI debe tener
            date
            punto_emision
                -> secuencial
                -> ambiente SRI
            datos
            Pasa a ser no editable
        """
        d = get_date()
        bill = self.get_bill()
        bill.date = d
        bill.punto_emision = self.punto_emision
        bill.status = SRIStatus.options.ReadyToSend
        bill.save()
        self.assertEquals(self.get_bill().status,
                          SRIStatus.options.ReadyToSend)

    def test_cant_modify_bill_not_proforma(self):
        """
        No se puede modificar una factura que no este en status='proforma'
        """
        bill = self.get_bill()
        bill.punto_emision = self.punto_emision
        bill.ambiente_sri = self.punto_emision.ambiente_sri
        bill.clave_acceso = '1234512345'
        bill.xml_content = '<xml></xml>'
        bill.status = SRIStatus.options.ReadyToSend
        bill.save()
        self.assertEquals(self.get_bill().status,
                          SRIStatus.options.ReadyToSend)

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
