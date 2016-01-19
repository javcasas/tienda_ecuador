# -*- coding: utf-8 -*-
from django import forms
import util.mail


class SalesContactForm(forms.Form):
    nombre_comercial = forms.CharField(
        label='Empresa',
        max_length=100)
    email = forms.EmailField(
        label="E-Mail de contacto")
    telefono = forms.CharField(
        label="Teléfono de contacto")
    mensaje = forms.CharField(
        label=u"Mensaje",
        max_length=5000,
        widget=forms.Textarea,
        )

    def send_email(self):
        msg_text = u'''
Peticion de Ventas
Empresa: {nombre_comercial}
Email: {email}
Telefono: {telefono}

{mensaje}
'''.format(**self.cleaned_data)
        util.mail.send_mail(
            from_="ventas@dssti.com",
            to="ventas@dssti.com",
            subject="Peticion de Ventas - {}".format(self.cleaned_data['nombre_comercial']),
            content=msg_text)


class SupportContactForm(forms.Form):
    url = forms.CharField(
        label='Nombre Comercial',
        widget=forms.HiddenInput,
        required=False)
    mensaje = forms.CharField(
        label="Problema",
        widget=forms.Textarea,
        max_length=500)

    def send_email(self, company, user):
        msg_text = u'''
Peticion de Soporte
Empresa: {company.id} - {company.nombre_comercial} - {company.razon_social}
Email: {user.email}
Url: {url}

{mensaje}
'''.format(company=company, user=user, **self.cleaned_data)
        util.mail.send_mail(
            from_="soporte@dssti.com",
            to="soporte@dssti.com",
            subject="Peticion de Soporte - {}".format(company.nombre_comercial),
            content=msg_text)
