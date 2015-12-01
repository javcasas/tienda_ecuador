from suds.client import Client
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
    result = client.service.validarComprobante(xml_data.encode('base64'))
    return result

def autorizar_comprobante(clave_acceso, entorno='pruebas'):
    client = Client(urls[entorno]['autorizacion'])
    result = client.service.autorizacionComprobante(clave_acceso)
    return result
