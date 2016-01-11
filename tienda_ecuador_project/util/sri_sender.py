from suds.client import Client
import logging
logger = logging.getLogger("sri.request")

urls = {
    'pruebas': {
        'recepcion': "https://celcer.sri.gob.ec/comprobantes-electronicos-ws/RecepcionComprobantes?wsdl",
        'autorizacion': 'https://celcer.sri.gob.ec/comprobantes-electronicos-ws/AutorizacionComprobantes?wsdl',
    },
    'produccion': {
        'recepcion': 'https://cel.sri.gob.ec/comprobantes-electronicos-ws/RecepcionComprobantesOffline?wsdl',
        'autorizacion': 'https://cel.sri.gob.ec/comprobantes-electronicos-ws/AutorizacionComprobantesOffline?wsdl',
    },
}


def enviar_comprobante(xml_data, entorno='pruebas'):
    client = Client(urls[entorno]['recepcion'])
    logger.info("enviar_comprobante {entorno} request: {xml}".format(xml=xml_data, entorno=entorno))
    result = client.service.validarComprobante(xml_data.encode('base64'))
    logger.info("enviar_comprobante {entorno} response: {res}".format(entorno=entorno, res=result))
    return result


def autorizar_comprobante(clave_acceso, entorno='pruebas'):
    client = Client(urls[entorno]['autorizacion'])
    logger.info("autorizar_comprobante {entorno} request: {clave}".format(clave=clave_acceso, entorno=entorno))
    result = client.service.autorizacionComprobante(clave_acceso)
    logger.info("autorizar_comprobante {entorno} response: {res}".format(entorno=entorno, res=result))
    return result
