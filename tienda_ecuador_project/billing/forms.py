# -*- coding: utf8 -*-
from django import forms
from billing import models


class ItemForm(forms.ModelForm):
    sku = forms.CharField(
        max_length=50,
        label='Código de stock (SKU)',
        help_text="Por favor teclee un código de stock.")
    name = forms.CharField(
        label='Nombre',
        max_length=50,
        help_text="Por favor teclee el nombre del artículo.")
    tipo = forms.ChoiceField(
        label='Tipo',
        choices=models.Item_tipo_OPTIONS,
        help_text="Por favor seleccione el tipo del artículo.")
    decimales_qty = forms.ChoiceField(
        label='Decimales en cantidad',
        choices=models.Item_decimales_OPTIONS)
    description = forms.CharField(
        label="Descripción",
        max_length=500,
        widget=forms.Textarea(),
        help_text="Por favor teclee una descripción.")
    unit_cost = forms.DecimalField(
        decimal_places=4,
        label="Coste por unidad",
        help_text='Por favor introduzca el coste por unidad.')
    unit_price = forms.DecimalField(
        decimal_places=4,
        label="Precio por unidad",
        help_text='Por favor introduzca el precio por unidad.')
    iva = forms.ModelChoiceField(
        label='IVA',
        queryset=models.Iva.objects,
        help_text='Por favor, seleccione el IVA del producto')
    ice = forms.ModelChoiceField(
        label='ICE',
        queryset=models.Ice.objects,
        required=False,
        empty_label='Sin ICE',
        help_text='Por favor, seleccione el ICE del producto')

    # An inline class to provide additional information on the form.
    class Meta:
        # Provide an association between the ModelForm and a model
        model = models.Item
        fields = ('sku', 'name', 'tipo', 'unit_price', 'unit_cost', 'description', 'decimales_qty')


class ProformaBillForm(forms.ModelForm):
    issued_to = forms.ModelChoiceField(
        label="Cliente",
        queryset=models.Customer.objects,
        help_text="Por favor seleccione el cliente.")
    number = forms.CharField(
        label="Identificador",
        max_length=50,
        help_text="Por favor teclee un código identificador para la proforma.")

    class Meta:
        # Provide an association between the ModelForm and a model
        model = models.ProformaBill
        fields = ('issued_to', 'number')


class CustomerForm(forms.ModelForm):
    razon_social = forms.CharField(
        label="Razón Social",
        max_length=50,
        help_text="Por favor teclee la razon social.")
    tipo_identificacion = forms.ChoiceField(
        label="Tipo de Identificación",
        choices=[('ruc', 'RUC'), ('cedula', 'Cedula')],
        help_text="Por favor seleccione el tipo de identificación.")
    identificacion = forms.CharField(
        label="Identificación",
        max_length=50,
        help_text="Por favor teclee la identificación.")
    email = forms.CharField(
        label="E-Mail",
        max_length=50,
        help_text="Por favor teclee el email.")
    direccion = forms.CharField(
        label="Dirección",
        max_length=50,
        help_text="Por favor teclee la dirección.")

    # An inline class to provide additional information on the form.
    class Meta:
        # Provide an association between the ModelForm and a model
        model = models.Customer
        fields = ('razon_social', 'tipo_identificacion',
                  'identificacion', 'email', 'direccion')


class ProformaBillAddItemForm(forms.ModelForm):
    qty = forms.DecimalField(
        decimal_places=4,
        label="Cantidad",
        initial=1,
        help_text='Por favor introduzca la cantidad.')
    copy_from = forms.ModelChoiceField(
        label='Artículo',
        queryset=None,
        help_text="Seleccione un artículo que añadir a la factura.")

    # An inline class to provide additional information on the form.
    class Meta:
        # Provide an association between the ModelForm and a model
        model = models.ProformaBillItem
        fields = ('qty', 'copy_from')


class ProformaBillItemForm(forms.ModelForm):
    sku = forms.CharField(
        label='Código de stock (SKU)',
        max_length=50,
        help_text="Por favor teclee un código de stock.")
    name = forms.CharField(
        label="Nombre",
        max_length=50,
        help_text="Por favor teclee el nombre del artículo.")
    unit_price = forms.DecimalField(
        label="Precio por unidad",
        help_text='Por favor introduzca el precio por unidad.')
    qty = forms.DecimalField(
        decimal_places=4,
        label="Cantidad",
        help_text='Por favor introduzca la cantidad.')
    description = forms.CharField(
        label="Descripción",
        max_length=500,
        widget=forms.Textarea(),
        help_text="Por favor teclee una descripción.")
    unit_cost = forms.DecimalField(
        widget=forms.HiddenInput())
    proforma_bill = forms.ModelChoiceField(
        queryset=models.ProformaBill.objects,
        widget=forms.HiddenInput())

    # An inline class to provide additional information on the form.
    class Meta:
        # Provide an association between the ModelForm and a model
        model = models.ProformaBillItem
        fields = ('sku', 'name', 'qty', 'unit_price', 'description',
                  'unit_cost', 'proforma_bill')



from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth import authenticate
from django.utils.translation import ugettext_lazy as _

class LoginForm(AuthenticationForm):
    username = forms.CharField(
        max_length=30,
        label='Usuario')
    password = forms.CharField(
        widget=forms.PasswordInput,
        label='Contraseña')

    error_messages = {
        'invalid_login': _(u"Usuario o Contraseña incorrectos. "
                           u"Tenga en cuenta que ambos campos son sensibles a mayúsculas y minúsculas"),
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
    username = forms.RegexField(label=_("Usuario"), max_length=30,
        regex=r'^[\w.@+-]+$',
        help_text=_(u"Requerido. Máximo 30 caracteres. Sólo letras, dígitos y"
                      "@/./+/-/_ ."),
        error_messages={
            'invalid': _(u"El usuario sólo puede contener letras, números  y caracteres "
                         "@/./+/-/_.")})
    password1 = forms.CharField(label=_(u"Contraseña"),
        widget=forms.PasswordInput)
    password2 = forms.CharField(label=_(u"Contraseña (repetir)"),
        widget=forms.PasswordInput,
        help_text=_(u"Introduzca la misma contraseña otra vez, para verificación."))
