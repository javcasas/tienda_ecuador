from suds.client import Client
urls = {
    'pruebas': {
        'recepcion': "https://celcer.sri.gob.ec/comprobantes-electronicos-ws/RecepcionComprobantes?wsdl",
        'autorizacion': 'https://celcer.sri.gob.ec/comprobantes-electronicos-ws/AutorizacionComprobantes?wsdl',
    },        
}

def enviar_comprobante(xml_data):
    client = Client(urls['pruebas']['recepcion'])
    result = client.service.validarComprobante(xml_data.encode('base64'))
    return result

def validar_comprobante(clave_acceso):
    client = Client(urls['pruebas']['autorizacion'])
    result = client.service.autorizacionComprobante(clave_acceso)
    print result.autorizaciones
