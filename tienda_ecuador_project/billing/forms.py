# -*- coding: utf-8 -*-
from django import forms
from inventory.models import Item_tipo_OPTIONS, Item_decimales_OPTIONS
import sri.models as sri
from billing import models


"""class ItemForm(forms.ModelForm):
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
        choices=Item_tipo_OPTIONS,
        help_text="Por favor seleccione el tipo del artículo.")
    decimales_qty = forms.ChoiceField(
        label='Decimales en cantidad',
        choices=Item_decimales_OPTIONS)
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
        queryset=sri.Iva.objects,
        help_text='Por favor, seleccione el IVA del producto')
    ice = forms.ModelChoiceField(
        label='ICE',
        queryset=sri.Ice.objects,
        required=False,
        empty_label='Sin ICE',
        help_text='Por favor, seleccione el ICE del producto')

    # An inline class to provide additional information on the form.
    class Meta:
        # Provide an association between the ModelForm and a model
        model = models.Item
        fields = ('sku', 'name', 'tipo', 'unit_price', 'unit_cost',
                  'description', 'decimales_qty')
"""

class BillForm(forms.ModelForm):
    issued_to = forms.ModelChoiceField(
        label="Cliente",
        queryset=models.Customer.objects,
        help_text="Por favor seleccione el cliente.")

    class Meta:
        # Provide an association between the ModelForm and a model
        model = models.Bill
        fields = ('issued_to',)

    def clean(self):
        if self.data.get('cons_final') == 'True':
            self.data = dict(self.data)
            c, created = models.Customer.objects.get_or_create(
                razon_social='CONSUMIDOR FINAL',
                tipo_identificacion='ruc',
                identificacion='9999999999999',
                company=self.instance.punto_emision.establecimiento.company)
            self.data['issued_to'] = str(c.id)
        return super(BillForm, self).clean()


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


class BillAddItemForm(forms.ModelForm):
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
        model = models.BillItem
        fields = ('qty', 'copy_from')


class BillItemForm(forms.ModelForm):
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
    bill = forms.ModelChoiceField(
        queryset=models.Bill.objects,
        widget=forms.HiddenInput())

    # An inline class to provide additional information on the form.
    class Meta:
        # Provide an association between the ModelForm and a model
        model = models.BillItem
        fields = ('sku', 'name', 'qty', 'unit_price', 'description',
                  'unit_cost', 'bill')

class SendToCustomerForm(forms.Form):
    subject = forms.CharField(
        label="Asunto",
        max_length=100,
        help_text="Por favor teclee un asunto.")
    text = forms.CharField(
        label="Cuerpo del Email",
        max_length=500,
        widget=forms.Textarea(),
        help_text="Por favor teclee una descripción.")
    class Meta:
        # Provide an association between the ModelForm and a model
        fields = ('subject', 'text',)
