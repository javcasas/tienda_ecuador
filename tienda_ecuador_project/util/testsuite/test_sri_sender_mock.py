# * coding: utf-8 *
import datetime

from django.test import TestCase


class ReadOnlyMixin(object):
    _is_read_only = False
    def _turn_read_only(self):
        self._is_read_only = True
        for item_name in dir(self):
            item = getattr(self, item_name)
            if issubclass(type(item), ReadOnlyMixin):
                item._turn_read_only()

    def __setattr__(self, name, val):
        if name == '_is_read_only':
            return super(ReadOnlyMixin, self).__setattr__(name, val)
        else:
            return self._op_if_not_read_only(
                lambda: super(ReadOnlyMixin, self).__setattr__(name, val)
            )

    def _op_if_not_read_only(self, op):
        if not self._is_read_only:
            return op()
        else:
            raise Exception("Read Only Object")


class GenericObject(ReadOnlyMixin):
    pass


class GenericList(ReadOnlyMixin, list):
    def _turn_read_only(self):
        self._is_read_only = True
        for item in self:
            if issubclass(type(item), ReadOnlyMixin):
                item._turn_read_only()

    def append(self, *args):
        return self._op_if_not_read_only(
            lambda: super(GenericList, self).append(*args)
        )


def gen_respuesta_solicitud_invalid_xml(clave_acceso):
    """
    (respuestaSolicitud){
       estado = "DEVUELTA"
       comprobantes =
          (comprobantes){
             comprobante[] =
                (comprobante){
                   claveAcceso = "2209201501170439497000120021000000146680001466819"
                   mensajes =
                      (mensajes){
                         mensaje[] =
                            (mensaje){
                               identificador = "35"
                               mensaje = "ARCHIVO NO CUMPLE ESTRUCTURA XML"
                               informacionAdicional = "El ambiente de la solicitud PRODUCCIÓN no coincide con el de ejecución PRUEBAS"
                               tipo = "ERROR"
                            },
                      }
                },
          }
     }
    """
    mock = GenericObject()
    mock.estado = 'DEVUELTA'
    mock.comprobantes = GenericObject()
    mock.comprobantes.comprobante = GenericList([GenericObject()])
    mock.comprobantes.comprobante[0].claveAcceso = clave_acceso
    mock.comprobantes.comprobante[0].mensajes = GenericObject()
    mock.comprobantes.comprobante[0].mensajes.mensaje = GenericList([GenericObject()])
    mock.comprobantes.comprobante[0].mensajes.mensaje[0].identificador = '35'
    mock.comprobantes.comprobante[0].mensajes.mensaje[0].mensaje = 'ARCHIVO NO CUMPLE ESTRUCTURA XML'
    mock.comprobantes.comprobante[0].mensajes.mensaje[0].informacionAdicional = 'El ambiente de la solicitud PRODUCCIÓN no coincide con el de ejecución PRUEBAS'
    mock.comprobantes.comprobante[0].mensajes.mensaje[0].tipo = 'ERROR'
    mock._turn_read_only()
    return mock


def gen_respuesta_autorizacion_no_hay_comprobantes(clave_acceso):
    """
    (respuestaComprobante){
       claveAccesoConsultada = "2209201501170439497000120021000000146680001466819"
       numeroComprobantes = "0"
       autorizaciones = ""
     }
    """
    mock = GenericObject()
    mock.claveAccesoConsultada = clave_acceso
    mock.numeroComprobantes = "0"
    mock.autorizaciones = ""
    mock._turn_read_only()
    return mock


def gen_respuesta_comprobante_valido(clave_acceso, comprobante, ambiente='pruebas'):
    """
    (respuestaComprobante){
       claveAccesoConsultada = "2209201501170439497000120021000000146680001466819"
       numeroComprobantes = "1"
       autorizaciones = 
          (autorizaciones){
             autorizacion[] = 
                (autorizacion){
                   estado = "AUTORIZADO"
                   numeroAutorizacion = "2309201501515617043949700019460282211"
                   fechaAutorizacion = 2015-09-23 01:51:56
                   ambiente = "PRODUCCIÓN"
                   comprobante = "[[ comprobante ]]"
                   mensajes = ""
                },
          }
     }
    """
    ambiente_str = {
        'pruebas': 'PRUEBAS',
        'produccion': "PRODUCCIÓN",
    }[ambiente]
    mock = GenericObject()
    mock.claveAccesoConsultada = clave_acceso
    mock.numeroComprobantes = "1"
    mock.autorizaciones = GenericObject()
    mock.autorizaciones.autorizacion = GenericList([GenericObject()])
    mock.autorizaciones.autorizacion[0].estado = 'AUTORIZADO'
    mock.autorizaciones.autorizacion[0].numeroAutorizacion = "2309201501515617043949700019460282211"
    mock.autorizaciones.autorizacion[0].fechaAutorizacion = datetime.datetime(2015, 9, 23, 1, 51, 56)
    mock.autorizaciones.autorizacion[0].ambiente = ambiente_str
    mock.autorizaciones.autorizacion[0].comprobante = comprobante
    mock.autorizaciones.autorizacion[0].mensajes = ""

    if ambiente == 'pruebas':
        mock.autorizaciones.autorizacion[0].mensajes = GenericObject()
        mock.autorizaciones.autorizacion[0].mensajes.mensaje = GenericList([GenericObject()])
        mock.autorizaciones.autorizacion[0].mensajes.mensaje[0].identificador = '60'
        mock.autorizaciones.autorizacion[0].mensajes.mensaje[0].mensaje = 'ESTE PROCESO FUE REALIZADO EN EL AMBIENTE DE PRUEBAS'
        mock.autorizaciones.autorizacion[0].mensajes.mensaje[0].tipo = 'ADVERTENCIA'

    mock._turn_read_only()
    return mock


class EnviarComprobanteMock(object):
    def __init__(self, response):
        self.response = response
        self.request_args = {}

    def __call__(self, xml_data, entorno='pruebas'):
        self.request_args['xml_data'] = xml_data
        self.request_args['entorno'] = entorno
        return self.response


class AutorizarComprobanteMock(object):
    def __init__(self, response):
        self.response = response
        self.request_args = {}

    def __call__(self, clave_acceso, entorno='pruebas'):
        self.request_args['clave_acceso'] = clave_acceso
        self.request_args['entorno'] = entorno
        return self.response


class SRISendMockTests(TestCase):
    def test_invalid_xml_response(self):
        clave_acceso = '2209201501170439497000120021000000146680001466819'
        mock = gen_respuesta_solicitud_invalid_xml(clave_acceso)
        self.assertEquals(mock.estado, 'DEVUELTA')
        self.assertEquals(mock.comprobantes.comprobante[0].claveAcceso, clave_acceso)
        self.assertEquals(mock.comprobantes.comprobante[0].mensajes.mensaje[0].identificador, '35')
        self.assertEquals(mock.comprobantes.comprobante[0].mensajes.mensaje[0].tipo, 'ERROR')
        with self.assertRaises(Exception):
            mock.comprobantes.comprobante.append("ASDF")

    def test_EnviarComprobanteMock(self):
        clave_acceso = '2209201501170439497000120021000000146680001466819'
        xml_data = '<xml></xml>'
        response = gen_respuesta_solicitud_invalid_xml(clave_acceso)
        entorno = 'produccion'

        mock_call = EnviarComprobanteMock(response)
        res = mock_call(xml_data, entorno=entorno)

        self.assertEquals(res, response)
        self.assertEquals(mock_call.request_args['xml_data'], xml_data)
        self.assertEquals(mock_call.request_args['entorno'], entorno)


class SRIAuthoriseMockTests(TestCase):
    def test_unknown_clave_acceso(self):
        clave_acceso = '2209201501170439497000120021000000146680001466819'
        mock = gen_respuesta_autorizacion_no_hay_comprobantes(clave_acceso)
        self.assertEquals(mock.claveAccesoConsultada, clave_acceso)
        self.assertEquals(mock.numeroComprobantes, '0')
        self.assertEquals(mock.autorizaciones, '')

    def test_comprobante_valido(self):
        clave_acceso = '2209201501170439497000120021000000146680001466819'
        comprobante = '<xml></xml>'
        mock = gen_respuesta_comprobante_valido(clave_acceso, comprobante, ambiente='pruebas')
        self.assertEquals(mock.claveAccesoConsultada, clave_acceso)
        self.assertEquals(mock.numeroComprobantes, '1')
        self.assertEquals(mock.autorizaciones.autorizacion[0].ambiente, 'PRUEBAS')
        self.assertEquals(mock.autorizaciones.autorizacion[0].comprobante, comprobante)
        self.assertEquals(mock.autorizaciones.autorizacion[0].estado, 'AUTORIZADO')
        self.assertEquals(mock.autorizaciones.autorizacion[0].mensajes.mensaje[0].identificador, '60')

    def test_comprobante_valido_produccion(self):
        clave_acceso = '2209201501170439497000120021000000146680001466819'
        comprobante = '<xml></xml>'
        mock = gen_respuesta_comprobante_valido(clave_acceso, comprobante, ambiente='produccion')
        self.assertEquals(mock.claveAccesoConsultada, clave_acceso)
        self.assertEquals(mock.numeroComprobantes, '1')
        self.assertEquals(mock.autorizaciones.autorizacion[0].ambiente, 'PRODUCCIÓN')
        self.assertEquals(mock.autorizaciones.autorizacion[0].comprobante, comprobante)
        self.assertEquals(mock.autorizaciones.autorizacion[0].estado, 'AUTORIZADO')
        if mock.autorizaciones.autorizacion[0].mensajes:
            for msg in mock.autorizaciones.autorizacion[0].mensajes.mensaje:
                if msg.identificador == '60':
                    self.fail("Mensaje de pruebas en produccion")

    def test_AutorizarComprobanteMock(self):
        clave_acceso = '2209201501170439497000120021000000146680001466819'
        xml_data = '<xml></xml>'
        entorno = 'produccion'
        response = gen_respuesta_comprobante_valido(clave_acceso, xml_data, ambiente=entorno)

        mock_call = AutorizarComprobanteMock(response)
        res = mock_call(clave_acceso, entorno=entorno)

        self.assertEquals(res, response)
        self.assertEquals(mock_call.request_args['clave_acceso'], clave_acceso)
        self.assertEquals(mock_call.request_args['entorno'], entorno)
