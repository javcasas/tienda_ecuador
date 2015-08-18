# -*- coding: utf8 -*-
from datetime import datetime
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

    # An inline class to provide additional information on the form.
    class Meta:
        # Provide an association between the ModelForm and a model
        model = models.Item
        fields = ('sku', 'name', 'unit_price', 'unit_cost', 'description')


class ProformaBillForm(forms.ModelForm):
    issued_to = forms.ModelChoiceField(
        label="Cliente",
        queryset=models.Customer.objects,
        help_text="Por favor seleccione el cliente.")
    number = forms.CharField(
        label="Identificador",
        max_length=50,
        help_text="Por favor teclee un código identificador para la proforma.")
    date = forms.DateTimeField(
        initial=datetime.utcnow,
        widget=forms.HiddenInput())

    class Meta:
        # Provide an association between the ModelForm and a model
        model = models.ProformaBill
        fields = ('issued_to', 'number', 'date')


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
    sku = forms.CharField(
        widget=forms.HiddenInput())
    name = forms.CharField(
        widget=forms.HiddenInput())
    description = forms.CharField(
        widget=forms.HiddenInput())
    qty = forms.IntegerField(
        label="Cantidad",
        initial=1,
        help_text='Por favor introduzca la cantidad.')
    unit_cost = forms.DecimalField(
        widget=forms.HiddenInput())
    unit_price = forms.DecimalField(
        widget=forms.HiddenInput())
    proforma_bill = forms.ModelChoiceField(
        queryset=models.ProformaBill.objects,
        widget=forms.HiddenInput())
    copy_from = forms.ModelChoiceField(
        label='Artículo',
        queryset=None,
        required=False,
        help_text="Seleccione un artículo que añadir a la factura.")

    # An inline class to provide additional information on the form.
    class Meta:
        # Provide an association between the ModelForm and a model
        model = models.ProformaBillItem
        fields = ('sku', 'name', 'description', 'qty', 'unit_cost',
                  'unit_price')


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
    qty = forms.IntegerField(
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
                  'unit_cost')
