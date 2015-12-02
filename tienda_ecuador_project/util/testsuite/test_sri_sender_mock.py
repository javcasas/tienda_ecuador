# * coding: utf-8 *
import datetime
from contextlib import contextmanager

from django.test import TestCase

from util import sri_sender


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

    def indented_str(self, indent=0):
        spaces = "  " * indent
        res = []
        for item_name, item_value in self.__dict__.iteritems():
            if item_name == '_is_read_only':
                continue
            try:
                res.extend(item_value.indented_str(indent+1))
            except:
                res.append("{}{} = {}".format(spaces, item_name, item_value))
        return res

    def __repr__(self):
        return "\n".join(self.indented_str()) + "\n"


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

    def indented_str(self, indent=0):
        spaces = "  " * indent
        res = []
        res.append("{}[".format(spaces))
        for i, item in enumerate(self):
            res.append("{}Index: {}".format(spaces, i))
            res.extend(item.indented_str(indent+1))
        res.append("{}]".format(spaces))
        return res


################################################
# respuestaSolicitud                           #
################################################
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


def gen_respuesta_solicitud_ok():
    """
    (respuestaSolicitud){
       estado = "RECIBIDA"
       comprobantes = ""
     }
    """
    mock = GenericObject()
    mock.estado = 'RECIBIDA'
    mock.comprobantes = ""
    mock._turn_read_only()
    return mock


################################################
# respuestaComprobante                         #
################################################
def gen_respuesta_autorizacion_clave_invalida(clave_acceso):
    """
    Si la clave no tiene los digitos necesarios

    (respuestaComprobante){
       claveAccesoConsultada = "123"
       autorizaciones =
          (autorizaciones){
             autorizacion[] =
                (autorizacion){
                   estado = "RECHAZADA"
                   mensajes =
                      (mensajes){
                         mensaje[] =
                            (mensaje){
                               identificador = "null"
                            },
                      }
                },
          }
     }
    """
    mock = GenericObject()
    mock.claveAccesoConsultada = clave_acceso
    mock.autorizaciones = GenericObject()
    mock.autorizaciones.autorizacion = GenericList([GenericObject()])
    mock.autorizaciones.autorizacion[0].estado = 'RECHAZADA'
    mock.autorizaciones.autorizacion[0].mensajes = GenericObject()
    mock.autorizaciones.autorizacion[0].mensajes.mensaje = GenericList([GenericObject()])
    mock.autorizaciones.autorizacion[0].mensajes.mensaje[0].identificador = 'null'
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


def gen_respuesta_autorizacion_comprobante_valido(clave_acceso, comprobante, ambiente='pruebas'):
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


@contextmanager
def MockEnviarComprobante(response):
    """
    Mocks the call
    """
    orig_enviar_call = sri_sender.enviar_comprobante
    orig_autorizar_call = sri_sender.autorizar_comprobante
    mock = EnviarComprobanteMock(response)
    sri_sender.enviar_comprobante = mock
    sri_sender.autorizar_comprobante = None
    yield mock
    sri_sender.enviar_comprobante = orig_enviar_call
    sri_sender.autorizar_comprobante = orig_autorizar_call


@contextmanager
def MockAutorizarComprobante(response):
    """
    Mocks the call
    """
    orig_enviar_call = sri_sender.enviar_comprobante
    orig_autorizar_call = sri_sender.autorizar_comprobante
    mock = AutorizarComprobanteMock(response)
    sri_sender.autorizar_comprobante = mock
    sri_sender.enviar_comprobante = None
    yield mock
    sri_sender.enviar_comprobante = orig_enviar_call
    sri_sender.autorizar_comprobante = orig_autorizar_call


@contextmanager
def MockSRISender(enviar_response, autorizar_response):
    """
    Mocks the whole module
    """
    orig_enviar_call = sri_sender.enviar_comprobante
    orig_autorizar_call = sri_sender.autorizar_comprobante
    mock_enviar = EnviarComprobanteMock(enviar_response)
    mock_autorizar = AutorizarComprobanteMock(autorizar_response)
    sri_sender.enviar_comprobante = mock_enviar
    sri_sender.autorizar_comprobante = mock_autorizar
    yield (mock_enviar, mock_autorizar)
    sri_sender.enviar_comprobante = orig_enviar_call
    sri_sender.autorizar_comprobante = orig_autorizar_call


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

    def test_EnviarComprobanteMock_context_manager(self):
        clave_acceso = '2209201501170439497000120021000000146680001466819'
        xml_data = '<xml></xml>'
        response = gen_respuesta_solicitud_invalid_xml(clave_acceso)
        entorno = 'produccion'

        with MockEnviarComprobante(response) as mock:
            res = sri_sender.enviar_comprobante(xml_data, entorno=entorno)

        self.assertEquals(res, response)
        self.assertEquals(mock.request_args['xml_data'], xml_data)
        self.assertEquals(mock.request_args['entorno'], entorno)


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
        mock = gen_respuesta_autorizacion_comprobante_valido(clave_acceso, comprobante, ambiente='pruebas')
        self.assertEquals(mock.claveAccesoConsultada, clave_acceso)
        self.assertEquals(mock.numeroComprobantes, '1')
        self.assertEquals(mock.autorizaciones.autorizacion[0].ambiente, 'PRUEBAS')
        self.assertEquals(mock.autorizaciones.autorizacion[0].comprobante, comprobante)
        self.assertEquals(mock.autorizaciones.autorizacion[0].estado, 'AUTORIZADO')
        self.assertEquals(mock.autorizaciones.autorizacion[0].mensajes.mensaje[0].identificador, '60')

    def test_comprobante_valido_produccion(self):
        clave_acceso = '2209201501170439497000120021000000146680001466819'
        comprobante = '<xml></xml>'
        mock = gen_respuesta_autorizacion_comprobante_valido(clave_acceso, comprobante, ambiente='produccion')
        self.assertEquals(mock.claveAccesoConsultada, clave_acceso)
        self.assertEquals(mock.numeroComprobantes, '1')
        self.assertEquals(mock.autorizaciones.autorizacion[0].ambiente, 'PRODUCCIÓN')
        self.assertEquals(mock.autorizaciones.autorizacion[0].comprobante, comprobante)
        self.assertEquals(mock.autorizaciones.autorizacion[0].estado, 'AUTORIZADO')
        if mock.autorizaciones.autorizacion[0].mensajes:
            for msg in mock.autorizaciones.autorizacion[0].mensajes.mensaje:
                if msg.identificador == '60':
                    self.fail("Mensaje de pruebas en produccion")

    def test_clave_invalida(self):
        clave_acceso = '123'
        mock = gen_respuesta_autorizacion_clave_invalida(clave_acceso)
        self.assertEquals(mock.claveAccesoConsultada, clave_acceso)
        self.assertEquals(mock.autorizaciones.autorizacion[0].estado, 'RECHAZADA')
        self.assertEquals(mock.autorizaciones.autorizacion[0].mensajes.mensaje[0].identificador, 'null')

    def test_AutorizarComprobanteMock(self):
        clave_acceso = '2209201501170439497000120021000000146680001466819'
        xml_data = '<xml></xml>'
        entorno = 'produccion'
        response = gen_respuesta_autorizacion_comprobante_valido(clave_acceso, xml_data, ambiente=entorno)

        mock_call = AutorizarComprobanteMock(response)
        res = mock_call(clave_acceso, entorno=entorno)

        self.assertEquals(res, response)
        self.assertEquals(mock_call.request_args['clave_acceso'], clave_acceso)
        self.assertEquals(mock_call.request_args['entorno'], entorno)

    def test_MockValidarComprobante(self):
        clave_acceso = '2209201501170439497000120021000000146680001466819'
        xml_data = '<xml></xml>'
        entorno = 'produccion'
        response = gen_respuesta_autorizacion_comprobante_valido(clave_acceso, xml_data, ambiente=entorno)

        with MockAutorizarComprobante(response) as mock:
            res = sri_sender.autorizar_comprobante(clave_acceso, entorno=entorno)

        self.assertEquals(res, response)
        self.assertEquals(mock.request_args['clave_acceso'], clave_acceso)
        self.assertEquals(mock.request_args['entorno'], entorno)


class FullModuleMockTests(TestCase):
    def test_full_context_manager(self):
        clave_acceso = '2209201501170439497000120021000000146680001466819'
        xml_data = '<xml></xml>'
        entorno = 'produccion'
        enviar_response = gen_respuesta_solicitud_invalid_xml(clave_acceso)
        autorizar_response = gen_respuesta_autorizacion_comprobante_valido(
            clave_acceso, xml_data, ambiente=entorno)

        with MockSRISender(enviar_response, autorizar_response) as (enviar_mock, autorizar_mock):
            sri_sender.enviar_comprobante(xml_data, entorno=entorno)
            sri_sender.autorizar_comprobante(clave_acceso, entorno=entorno)

        self.assertEquals(autorizar_mock.request_args['clave_acceso'], clave_acceso)
        self.assertEquals(autorizar_mock.request_args['entorno'], entorno)

        self.assertEquals(enviar_mock.request_args['xml_data'], xml_data)
        self.assertEquals(enviar_mock.request_args['entorno'], entorno)
