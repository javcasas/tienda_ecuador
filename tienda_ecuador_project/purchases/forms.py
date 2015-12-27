# -*- coding: utf-8 -*-
import time
import xml.etree.ElementTree as ET

from django import forms
from company_accounts import models
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ValidationError

from util import signature

def test_xml_content(text):
    try:
        tree = ET.fromstring(text)
    except ET.ParseError:
        raise Exception("Fichero XML incorrecto")

    tests = [("infoTributaria/ambiente", "No hay ambiente"),
             ("./infoTributaria/razonSocial", u"No hay razón social"),
             ("./infoTributaria/nombreComercial", "No hay nombre comercial"),
             ("./infoTributaria/ruc", "No hay RUC"),
             ("./infoTributaria/claveAcceso", "No hay clave de acceso")
    ]
    errors = []
    for test, err_msg in tests:
        if tree.find(test) is None:
            raise Exception(err_msg)

    if tree.find("infoTributaria/ambiente").text != "2":
        raise Exception("El ambiente SRI no es PRODUCCION")

def get_xml_content(text):
    try:
        test_xml_content(text)
        return text
    except:
        pass

    try:
        tree = ET.fromstring(text)
        new_data = tree.find("comprobante").text
        test_xml_content(new_data)
        return new_data
    except AttributeError:
        raise Exception("Fichero XML incorrecto")


class PurchaseCreateFromXMLForm(forms.Form):
    xml_content = forms.FileField(
        label='Cargar XML',
        help_text='Cargar la factura en formato XML')

    def clean(self):
        cleaned_data = super(PurchaseCreateFromXMLForm, self).clean()
        try:
            cleaned_data['xml_content']
        except KeyError:
            return cleaned_data

        xml_content = cleaned_data['xml_content'].read()
        cleaned_data['xml_content'].seek(0)

        try:
            xml_content = get_xml_content(xml_content)
            cleaned_data['xml_content_text'] = xml_content
        except Exception as e:
            self.add_error("xml_content",
                           "Fichero XML incorrecto")
        return cleaned_data
