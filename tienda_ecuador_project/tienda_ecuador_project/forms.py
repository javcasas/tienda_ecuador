# -*- coding: utf-8 -*-
from email.mime.text import MIMEText
from subprocess import Popen, PIPE

from django import forms


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
        max_length=5000)

    def send_email(self):
        msg_text = u'''
Peticion de Ventas
Empresa: {nombre_comercial}
Email: {email}
Telefono: {telefono}

{mensaje}
'''
        msg = MIMEText(msg_text.format(**self.cleaned_data))
        msg["From"] = "ventas@dssti.com"
        msg["To"] = "ventas@dssti.com"
        msg["Subject"] = "Peticion de Ventas - {}".format(self.cleaned_data['nombre_comercial'])
        p = Popen(["/usr/bin/sendmail", "-t", "-oi"], stdin=PIPE)
        p.communicate(msg.as_string())


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
'''
        msg = MIMEText(msg_text.format(company=company, user=user, **self.cleaned_data))
        msg["From"] = "soporte@dssti.com"
        msg["To"] = "soporte@dssti.com"
        msg["Subject"] = "Peticion de Soporte - {}".format(company.nombre_comercial)
        p = Popen(["/usr/bin/sendmail", "-t", "-oi"], stdin=PIPE)
        p.communicate(msg.as_string())
