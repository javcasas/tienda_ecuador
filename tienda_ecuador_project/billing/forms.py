from datetime import datetime
from django import forms
from billing.models import (Item, Customer, ProformaBill,
                            ProformaBillItem, Company, Bill,
                            BillItem, Iva, Ice)


class ItemForm(forms.ModelForm):
    sku = forms.CharField(
        max_length=50,
        help_text="Please enter the SKU.")
    name = forms.CharField(
        max_length=50,
        help_text="Please enter the name of the item.")
    description = forms.CharField(
        max_length=500,
        help_text="Please enter the description.")
    iva = forms.ModelChoiceField(
        queryset=Iva.objects,
        help_text="Please select the IVA.")
    ice = forms.ModelChoiceField(
        queryset=Ice.objects,
        help_text="Please select the ICE.")
    unit_cost = forms.DecimalField(
        decimal_places=4,
        help_text="Please enter the unit cost.")
    unit_price = forms.DecimalField(
        decimal_places=4,
        help_text="Please enter the unit price.")

    # An inline class to provide additional information on the form.
    class Meta:
        # Provide an association between the ModelForm and a model
        model = Item
        fields = ('sku', 'name', 'description', 'iva', 'ice',
                  'unit_cost', 'unit_price')


class ProformaBillForm(forms.ModelForm):
    issued_to = forms.ModelChoiceField(
        queryset=None,
        help_text="Please select the customer.")
    number = forms.CharField(
        max_length=50,
        help_text="Please enter the number of the bill.")
    date = forms.DateTimeField(
        initial=datetime.utcnow,
        help_text='Please select the date')

    class Meta:
        # Provide an association between the ModelForm and a model
        model = ProformaBill
        fields = ('issued_to', 'number', 'date')


class BillItemForm(forms.ModelForm):
    sku = forms.CharField(
        max_length=50,
        help_text="Please enter the SKU.")
    name = forms.CharField(
        max_length=50,
        help_text="Please enter the name of the item.")
    description = forms.CharField(
        max_length=500,
        help_text="Please enter the description.")
    qty = forms.IntegerField(
        help_text='Please enter the quantity')
    bill = forms.ModelChoiceField(
        widget=forms.HiddenInput,
        queryset=Bill.objects.all(),
        help_text="Please select the bill.")
    company = forms.ModelChoiceField(
        widget=forms.HiddenInput,
        queryset=Company.objects.all(),
        help_text="Please select the company.")

    # An inline class to provide additional information on the form.
    class Meta:
        # Provide an association between the ModelForm and a model
        model = BillItem
        fields = ('sku', 'name', 'description', 'qty', 'bill', 'company')


class CustomerForm(forms.ModelForm):
    razon_social = forms.CharField(
        max_length=50,
        help_text="Por favor teclee la razon social.")
    tipo_identificacion = forms.ChoiceField(
        choices=[('ruc', 'RUC'), ('cedula', 'Cedula')],
        help_text="Por favor teclee la razon social.")
    identificacion = forms.CharField(
        max_length=50,
        help_text="Por favor teclee la identificacion.")
    email = forms.CharField(
        max_length=50,
        help_text="Por favor teclee el email.")
    direccion = forms.CharField(
        max_length=50,
        help_text="Por favor teclee la direccion.")

    # An inline class to provide additional information on the form.
    class Meta:
        # Provide an association between the ModelForm and a model
        model = Customer
        fields = ('razon_social', 'tipo_identificacion',
                  'identificacion', 'email', 'direccion')


class ProformaBillAddItemForm(forms.ModelForm):
    sku = forms.CharField(
        max_length=50,
        help_text="Please enter the SKU.",
        widget=forms.HiddenInput())
    name = forms.CharField(
        max_length=50,
        help_text="Please enter the name of the item.",
        widget=forms.HiddenInput())
    description = forms.CharField(
        max_length=500,
        help_text="Please enter the description.",
        widget=forms.HiddenInput())
    qty = forms.IntegerField(
        help_text='Please enter the quantity')
    unit_cost = forms.DecimalField(
        widget=forms.HiddenInput())
    unit_price = forms.DecimalField(
        widget=forms.HiddenInput())
    iva = forms.ModelChoiceField(
        queryset=Iva.objects,
        widget=forms.HiddenInput())
    ice = forms.ModelChoiceField(
        queryset=Ice.objects,
        widget=forms.HiddenInput())
    proforma_bill = forms.ModelChoiceField(
        queryset=ProformaBill.objects,
        widget=forms.HiddenInput())
    copy_from = forms.ModelChoiceField(
        queryset=None,
        required=False,
        help_text="Please select the item to copy from.")

    # An inline class to provide additional information on the form.
    class Meta:
        # Provide an association between the ModelForm and a model
        model = ProformaBillItem
        fields = ('sku', 'name', 'description', 'qty', 'unit_cost',
                  'unit_price', 'iva', 'ice')


class ProformaBillItemForm(forms.ModelForm):
    sku = forms.CharField(
        max_length=50,
        help_text="Please enter the SKU.")
    name = forms.CharField(
        max_length=50,
        help_text="Please enter the name of the item.")
    description = forms.CharField(
        max_length=500,
        help_text="Please enter the description.")
    qty = forms.IntegerField(
        help_text='Please enter the quantity')
    unit_cost = forms.DecimalField()
    unit_price = forms.DecimalField()
    iva = forms.ModelChoiceField(
        queryset=Iva.objects)
    ice = forms.ModelChoiceField(
        queryset=Ice.objects)
    proforma_bill = forms.ModelChoiceField(
        queryset=ProformaBill.objects,
        widget=forms.HiddenInput())

    # An inline class to provide additional information on the form.
    class Meta:
        # Provide an association between the ModelForm and a model
        model = ProformaBillItem
        fields = ('sku', 'name', 'description', 'qty', 'unit_cost',
                  'unit_price', 'iva', 'ice')
