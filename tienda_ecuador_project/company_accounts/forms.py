# -*- coding: utf8 -*-
from django import forms
from company_accounts import models
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.utils.translation import ugettext_lazy as _


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


class LoginForm(AuthenticationForm):
    username = forms.CharField(
        max_length=30,
        label='Usuario')
    password = forms.CharField(
        widget=forms.PasswordInput,
        label='Contraseña')

    error_messages = {
        'invalid_login': _(u"Usuario o Contraseña incorrectos. "
                           u"Tenga en cuenta que ambos campos son"
                           u" sensibles a mayúsculas y minúsculas"),
        'no_cookies': _(u"Su Navegador Web no tiene activadas las cookies. "
                        u"Actívelas para entrar al sistema."),
        'inactive': _(u"Esta cuenta está inactiva."),
    }


class MyUserCreationForm(UserCreationForm):
    """
    A form that creates a user, with no privileges, from the given username and
    password.
    """
    error_messages = {
        'duplicate_username': _("Ya hay un usuario con ese nombre."),
        'password_mismatch': _(u"Los dos campos de contraseña no coinciden."),
    }
    username = forms.RegexField(
        label=_("Usuario"),
        max_length=30,
        regex=r'^[\w.@+-]+$',
        help_text=_(u"Requerido. Máximo 30 caracteres. Sólo letras, dígitos y"
                    u"@/./+/-/_ ."),
        error_messages={
            'invalid': _(u"El usuario sólo puede contener letras, números "
                         "y caracteres @/./+/-/_.")})
    password1 = forms.CharField(
        label=_(u"Contraseña"),
        widget=forms.PasswordInput)
    password2 = forms.CharField(
        label=_(u"Contraseña (repetir)"),
        widget=forms.PasswordInput,
        help_text=_(u"Introduzca la misma contraseña otra vez, "
                    u"para verificación."))
