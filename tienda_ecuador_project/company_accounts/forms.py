# -*- coding: utf-8 -*-
import time
from django import forms
from company_accounts import models
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ValidationError

from util import signature


sample_xml = """<?xml version="1.0" ?>
<factura id="comprobante" version="1.1.0">
</factura>
"""


class CompanyForm(forms.ModelForm):
    nombre_comercial = forms.CharField(
        label='Nombre Comercial',
        max_length=100)
    ruc = forms.CharField(
        label="RUC",
        max_length=100)
    razon_social = forms.CharField(
        label=u"Razón Social",
        max_length=100)
    direccion_matriz = forms.CharField(
        label=u"Dirección Matriz",
        max_length=100)

    # An inline class to provide additional information on the form.
    class Meta:
        # Provide an association between the ModelForm and a model
        model = models.Company
        fields = ('razon_social', 'nombre_comercial', 'ruc',
                  'direccion_matriz')


class CertificateForm(forms.Form):
    cert = forms.FileField(
        label='Certificado')
    cert_key = forms.CharField(
        widget=forms.PasswordInput,
        label='Contraseña del Certificado')

    def clean(self):
        cleaned_data = super(CertificateForm, self).clean()
        cert_key = cleaned_data['cert_key']
        cert_data = cleaned_data['cert'].read()
        # Try signing
        test_id = "test{}".format(hash(self))
        try:
            signature.add_cert(test_id, "test", cert_data, cert_key)
            if signature.sign(test_id, "test", sample_xml) is None:
                raise ValidationError(u'Contraseña incorrecta',
                                      code='invalid_key')
            else:
                cleaned_data['cert_data'] = cert_data
        finally:
            raised = True
            while raised:
                try:
                    signature.del_cert(test_id, "test")
                    raised = False
                except:
                    time.sleep(0.1)
        return cleaned_data


class PuntoEmisionForm(forms.ModelForm):
    descripcion = forms.CharField(
        label='Descripción',
        max_length=50)
    codigo = forms.CharField(
        label="Código",
        max_length=3)
    siguiente_secuencial_pruebas = forms.IntegerField(
        label=u"Siguiente Secuencial de Pruebas")
    siguiente_secuencial_produccion = forms.IntegerField(
        label=u"Siguiente Secuencial de Producción")
    ambiente_sri = forms.ChoiceField(
        label="Ambiente SRI",
        choices=models.ambiente_sri_OPTIONS)

    # An inline class to provide additional information on the form.
    class Meta:
        # Provide an association between the ModelForm and a model
        model = models.PuntoEmision
        fields = ('descripcion', 'codigo', 'ambiente_sri',
                  'siguiente_secuencial_pruebas',
                  'siguiente_secuencial_produccion', )
