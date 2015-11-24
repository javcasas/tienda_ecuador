from django.test import TestCase
from util.property import Property, ConvertedProperty, ProtectedSetattr

import suds
from util.sri_sender import urls
from util import sri_sender


class WsdlUrlTests(TestCase):
    """
    Checks the URLs are valid
    """
    def valid_url(self, url, method_name):
        c = suds.client.Client(url)
        getattr(c.service, method_name)

    def test_pruebas_recepcion(self):
        self.valid_url(urls['pruebas']['recepcion'], 'validarComprobante')

    def test_pruebas_autorizacion(self):
        self.valid_url(urls['pruebas']['autorizacion'], 'autorizacionComprobante')

    def test_produccion_recepcion(self):
        self.valid_url(urls['produccion']['recepcion'], 'validarComprobante')

    def test_produccion_autorizacion(self):
        self.valid_url(urls['produccion']['autorizacion'], 'autorizacionComprobante')

    def test_invalid_pruebas_recepcion(self):
        with self.assertRaises(suds.transport.TransportError):
            self.valid_url(urls['pruebas']['recepcion'] + "sdf", 'validarComprobante')
        with self.assertRaises(Exception):
            self.valid_url("https://celcer.sri.gob.ec/", 'validarComprobante')


class SRISenderTests(TestCase):
    """
    Checks the sri_sender methods
    """
    def test_pruebas_recepcion(self):
        res = sri_sender.enviar_comprobante("<xml></xml")
        self.assertEquals(res.comprobantes.comprobante[0].claveAcceso, 'N/A')
        self.assertEquals(res.comprobantes.comprobante[0].mensajes.mensaje[0].identificador, '35')
        self.assertEquals(res.comprobantes.comprobante[0].mensajes.mensaje[0].mensaje, 'ARCHIVO NO CUMPLE ESTRUCTURA XML')

    def test_pruebas_autorizacion(self):
        res = sri_sender.validar_comprobante("123456")
        self.assertEquals(res.claveAccesoConsultada, '123456')
        self.assertEquals(res.autorizaciones.autorizacion[0].estado, 'RECHAZADA')
        self.assertEquals(res.autorizaciones.autorizacion[0].mensajes.mensaje[0].identificador, 'null')

    def test_produccion_recepcion(self):
        res = sri_sender.enviar_comprobante("<xml></xml", entorno='produccion')
        self.assertEquals(res.comprobantes.comprobante[0].claveAcceso, 'N/A')
        self.assertEquals(res.comprobantes.comprobante[0].mensajes.mensaje[0].identificador, '35')
        self.assertEquals(res.comprobantes.comprobante[0].mensajes.mensaje[0].mensaje, 'ARCHIVO NO CUMPLE ESTRUCTURA XML')

    def test_produccion_autorizacion(self):
        res = sri_sender.validar_comprobante("123456", entorno='produccion')
        self.assertEquals(res.claveAccesoConsultada, '123456')
        self.assertEquals(res.autorizaciones.autorizacion[0].estado, 'RECHAZADA')
        self.assertEquals(res.autorizaciones.autorizacion[0].mensajes.mensaje[0].identificador, 'null')
