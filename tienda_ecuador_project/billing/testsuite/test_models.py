from datetime import datetime
from itertools import count
from decimal import Decimal
import pytz

from django.test import TestCase
from django.core.exceptions import ValidationError

from billing.models import (ReadOnlyObject,
                            Company,
                            CompanyUser,
                            ProformaBill,
                            Bill,
                            Item,
                            ProformaBillItem,
                            Customer,
                            Iva, Ice,
                            ItemInBill,
                            Establecimiento,
                            PuntoEmision,
                            ClaveAcceso)

from billing import models

from helpers import (add_instance,
                     add_User,
                     add_Company,
                     add_ProformaBill,
                     add_Bill,
                     add_Customer,
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
        "ambiente_sri": "pruebas",
        'siguiente_comprobante_pruebas': 1,
        'siguiente_comprobante_produccion': 1,
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
    "BaseBill": {
        'number': '3',
        'date': get_date(),
        'xml_content': '',
        'ride_content': '',
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
        'cantidad': 100,
    },
}


class FieldsTests(TestCase, TestHelpersMixin):
    """
    Tests that check if a given model has all the required fields
    """
    def setUp(self):
        self.company = add_Company(**base_data['Company'])

        self.establecimiento = add_instance(Establecimiento,
                                            company=self.company,
                                            **base_data['Establecimiento'])

        self.punto_emision = add_instance(PuntoEmision,
                                          establecimiento=self.establecimiento,
                                          **base_data['PuntoEmision'])

        self.user = add_User(username="Paco", password='')

        self.customer = add_Customer(
            **dict(base_data['BaseCustomer'], company=self.company))

        self.proforma_bill = add_ProformaBill(
            **dict(base_data['BaseBill'],
                   punto_emision=self.punto_emision,
                   issued_to=self.customer))

        self.bill = add_Bill(
            **dict(base_data['BaseBill'],
                   company=self.company))

        self.iva = add_instance(Iva, **dict(base_data['Iva']))
        self.ice = add_instance(Ice, **dict(base_data['Ice']))
        self.forma_pago = add_instance(
            models.FormaPago, **base_data['FormaPago'])
        self.plazo_pago = add_instance(
            models.PlazoPago, **base_data['PlazoPago'])

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
            (ProformaBill, base_data['BaseBill'],
                {'punto_emision': self.punto_emision,
                 'issued_to': self.customer}),
            (Bill, base_data['BaseBill'],
                {'company': self.company}),
            (Item, base_data['BaseItem'],
                {"company": self.company,
                 }),
            (ProformaBillItem, base_data['BaseItem'],
                {"proforma_bill": self.proforma_bill,
                 'qty': 6}),
            (models.FormaPago, base_data['FormaPago'],
                {}),
            (models.PlazoPago, base_data['PlazoPago'],
                {}),
            (models.Pago, base_data['Pago'],
                {'forma_pago': self.forma_pago,
                 'plazo_pago': self.plazo_pago,
                 'bill': self.proforma_bill}),
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


class ReadOnlyTests(TestCase, TestHelpersMixin):
    """
    Test that checks that a final model can be created,
    but not modified
    """
    def setUp(self):
        self.company = Company.objects.get_or_create(**base_data['Company'])[0]
        self.tests = [
            (Bill,
                {'number': '3',
                 'date': get_date(),
                 'company': self.company})
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


class CompanyUserTests(TestCase, TestHelpersMixin):
    def setUp(self):
        self.company = add_Company(**base_data['Company'])
        self.user = add_User(username="Paco", password='')
        self.company_user = add_instance(CompanyUser,
                                         company=self.company,
                                         user=self.user)

    def test_unicode(self):
        self.assertEquals(str(self.company_user),
                          self.company_user.user.username)


class ProformaToFinalTests(TestCase, TestHelpersMixin):
    """
    Tests that check converting a proforma into a final
    """
    def setUp(self):
        self.company = add_Company(
            nombre_comercial="Tienda 1", ruc='1234567890001',
            razon_social="Paco Pil", direccion_matriz="C del pepino",
            contribuyente_especial="")
        self.establecimiento = add_instance(Establecimiento,
                                            company=self.company,
                                            **base_data['Establecimiento'])
        self.punto_emision = add_instance(PuntoEmision,
                                          establecimiento=self.establecimiento,
                                          **base_data['PuntoEmision'])
        self.user = add_User(username="Paco", password='')

    def test_ProformaBill_to_Bill(self):
        proforma = ProformaBill(
            issued_to=Customer.objects.get_or_create(
                company=self.company,
                **base_data['BaseCustomer'])[0],
            date=get_date(),
            punto_emision=self.punto_emision,
            xml_content='bleh' * 1000,     # 4KB
            ride_content='blah' * 100000,  # 400KB
            number='3')
        proforma.save()
        bill = Bill.fromProformaBill(proforma)
        for field in ['number', 'date', 'xml_content', 'ride_content']:
            v1 = getattr(bill, field)
            v2 = getattr(proforma, field)
            self.assertEquals(
                v1, v2,
                "Field '{}' is different: {} != {}".format(
                    field, repr(v1), repr(v2)))
        self.assertEquals(
            bill.company,
            proforma.punto_emision.establecimiento.company)


class ItemTests(TestCase, TestHelpersMixin):
    """
    Tests for the Item classes
    """
    def test_total_sin_impuestos(self):
        """
        Prueba el atributo "total_sin_impuestos"
        que devuelve el total correspondiente a un item
        sin contar los impuestos
        """
        item = ItemInBill(sku="1234", name="asdf", description="asdf",
                          unit_cost=10, unit_price=14, qty=6)
        self.assertEquals(item.total_sin_impuestos, 6 * 14)

    def test_bill_item_iva_ice(self):
        """
        Prueba los calculos de iva e ice
        """
        iva = add_instance(Iva, descripcion="12%", codigo="12", porcentaje=12)
        ice = add_instance(Ice, descripcion="Gaseosas",
                           codigo="145", grupo=1, porcentaje=50)
        proforma = ItemInBill(
            sku="1234", name="asdf", description="asdf", unit_cost=10,
            unit_price=10, qty=6)
        proforma.save()
        proforma.tax_items.add(iva, ice)

        # ICE
        self.assertEquals(proforma.base_imponible_ice,
                          proforma.total_sin_impuestos)
        valor_ice = proforma.base_imponible_ice * Decimal("0.5")
        self.assertEquals(proforma.valor_ice, valor_ice)

        # IVA
        self.assertEquals(proforma.base_imponible_iva,
                          proforma.total_sin_impuestos + valor_ice)
        valor_iva = proforma.base_imponible_iva * Decimal("0.12")
        self.assertEquals(proforma.valor_iva, valor_iva)
        self.assertEquals(proforma.total_impuestos, valor_iva + valor_ice)

    def test_unicode(self):
        """
        Prueba str() y unicode()
        """
        ob = Item(sku="1234", name="asdf", description="asdf",
                  unit_cost=10, unit_price=10)
        self.assertEquals(str(ob), "1234 - asdf")

    def test_increment(self):
        """
        Prueba str() y unicode()
        """
        ob = Item(sku="1234", name="asdf", description="asdf",
                  unit_cost=10, unit_price=10, decimales_qty=2)
        self.assertEquals(ob.increment_qty, "0.01")

    def test_increment_no_decimals(self):
        """
        Prueba str() y unicode()
        """
        ob = ProformaBillItem(sku="1234", name="asdf", description="asdf",
                  unit_cost=10, unit_price=10, decimales_qty=0)
        self.assertEquals(ob.increment_qty, "1")


class IdentificacionTests(TestCase):
    def setUp(self):
        self.company = add_Company(
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


class ProformaBillTest(TestCase, TestHelpersMixin):
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
        self.proforma = add_instance(ProformaBill,
                                     punto_emision=self.punto_emision,
                                     number='3',
                                     date=get_date(),
                                     issued_to=self.customer)
        for i in range(1, 5):
            ob = add_instance(ProformaBillItem,
                              proforma_bill=self.proforma,
                              sku='T123{}'.format(i),
                              name='Widget{}'.format(i),
                              description='Widget description',
                              qty=i,
                              unit_cost=5,
                              unit_price=10,)
            ob.tax_items.add(self.iva, self.ice)
        self.payment = add_instance(
            models.Pago,
            cantidad=Decimal(50),
            bill=self.proforma,
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
        self.assertEquals(self.proforma.subtotal,
                          {12: (1 + 2 + 3 + 4) * (10 + 5),
                           0: 0})
        for k, v in self.proforma.subtotal.iteritems():
            self.assertEquals(type(v), Decimal)

    def test_total_sin_impuestos(self):
        self.assertEquals(self.proforma.total_sin_impuestos,
                          (1 + 2 + 3 + 4) * 10)
        self.assertEquals(type(self.proforma.total_sin_impuestos), Decimal)

    def test_total_con_impuestos(self):
        self.assertEquals(self.proforma.total_con_impuestos,
                          (1 + 2 + 3 + 4) * (10 + 5) * Decimal("1.12"))
        self.assertEquals(type(self.proforma.total_con_impuestos), Decimal)

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
        self.assertEquals(self.proforma.impuestos, expected)

    def test_iva(self):
        unidades = 1 + 2 + 3 + 4
        precio_unitario = 10
        factor_ice = 1.5
        factor_iva = 0.12
        total = (unidades * precio_unitario) * factor_ice * factor_iva
        self.assertEquals(
            self.proforma.iva,
            {
                Decimal(0): Decimal(0),
                Decimal(12): Decimal(total),
            })
        self.assertEquals(type(self.proforma.iva[0]), Decimal)
        self.assertEquals(type(self.proforma.iva[12]), Decimal)

    def test_clave_acceso_encode(self):
        c = ClaveAcceso()
        c.fecha_emision = (2015, 7, 3)
        c.tipo_comprobante = "factura"
        c.ruc = "1790746119001"
        c.ambiente = "produccion"
        c.serie = 23013
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
        self.assertEquals(list(self.proforma.payment),
                          [self.payment])


class IceTests(TestCase, TestHelpersMixin):
    def setUp(self):
        self.ice = add_instance(Ice,
                                descripcion="Gaseosas",
                                grupo=3,
                                codigo="asdf",
                                porcentaje=50)

    def test_nonzero(self):
        self.assertTrue(self.ice)
        self.assertFalse(
            add_instance(Ice,
                         descripcion="No ICE", grupo=0,
                         codigo="", porcentaje=0))
