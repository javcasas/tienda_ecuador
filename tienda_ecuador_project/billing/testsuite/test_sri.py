# * encoding: utf8 *

from django.test import TestCase
from billing.sri import BillXmlData


class InfoTributariaTests(TestCase):
    def test_ambiente(self):
        tests = {
            "pruebas": 1,
            "produccion": 2,
        }
        info = BillXmlData.InfoTributaria()
        for k, v in tests.iteritems():
            info.ambiente = k
            self.assertEquals(info.ambiente.code, v)
        with self.assertRaises(ValueError):
            info.ambiente = "otro"


class InfoFacturaTests(TestCase):
    def test_tipo_identificacion_comprador(self):
        tests = [
            # Tipo, codigo, valido, invalidos
            ("ruc", 4, "1713831152001",
                ["555555",          # Un numero al azar
                 "1713831153001"]),  # Verificador invalido
            ("cedula", 5, "171383115-2",
                ["1713831152",  # cedula sin guion
                 "171383115-5",  # verificador incorrecto
                 "551383115-2",  # Provincia no existe
                 "5435345"]),    # un numero al azar
            ("pasaporte", 6, "AAF462110",
                []),
            ("consumidor_final", 7, "999999999",
                ["5435345"]),  # Todos los consumidores finales usan de identificacion 999999999
        ]
        for tipo, codigo, valor_valido, valores_invalidos in tests:
            info = BillXmlData.InfoFactura()
            info.tipo_identificacion_comprador = tipo
            self.assertEquals(info.tipo_identificacion_comprador.code, codigo)
            info.identificacion_comprador = valor_valido
            for v_invalido in valores_invalidos:
                try:
                    with self.assertRaises(ValueError):
                        info.identificacion_comprador = v_invalido
                except AssertionError:
                    raise AssertionError("ValueError not raised: {} {}".format(tipo, v_invalido))


class ImpuestoTests(TestCase):
    def test_codigo_porcentaje(self):
        imp = BillXmlData.Detalle.Impuesto()
        imp.codigo = 'iva'
        imp.codigo_porcentaje = '12%'
        self.assertEquals(imp.codigo_porcentaje.code, 2)
        self.assertEquals(imp.codigo_porcentaje.name, "12%")
        self.assertEquals(imp.codigo_porcentaje.value, 12)
        imp.codigo = 'ice'
        imp.codigo_porcentaje = "Cocinas, calefones y otros de uso doméstico a gas SENAE"
        self.assertEquals(imp.codigo_porcentaje.code, 3770)
        self.assertEquals(imp.codigo_porcentaje.name, "Cocinas, calefones y otros de uso doméstico a gas SENAE")
        self.assertEquals(imp.codigo_porcentaje.value, None)
