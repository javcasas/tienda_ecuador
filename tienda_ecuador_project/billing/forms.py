from datetime import datetime
from django import forms
from billing import models


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
    unit_cost = forms.DecimalField(
        decimal_places=4,
        help_text="Please enter the unit cost.")
    unit_price = forms.DecimalField(
        decimal_places=4,
        help_text="Please enter the unit price.")

    # An inline class to provide additional information on the form.
    class Meta:
        # Provide an association between the ModelForm and a model
        model = models.Item
        fields = ('sku', 'name', 'description',
                  'unit_cost', 'unit_price')


class ProformaBillForm(forms.ModelForm):
    issued_to = forms.ModelChoiceField(
        queryset=models.Customer.objects,
        help_text="Please select the customer.")
    number = forms.CharField(
        max_length=50,
        help_text="Please enter the number of the bill.")
    date = forms.DateTimeField(
        initial=datetime.utcnow,
        help_text='Please select the date')

    class Meta:
        # Provide an association between the ModelForm and a model
        model = models.ProformaBill
        fields = ('issued_to', 'number', 'date')


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
        model = models.Customer
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
    proforma_bill = forms.ModelChoiceField(
        queryset=models.ProformaBill.objects,
        widget=forms.HiddenInput())
    copy_from = forms.ModelChoiceField(
        queryset=None,
        required=False,
        help_text="Please select the item to copy from.")

    # An inline class to provide additional information on the form.
    class Meta:
        # Provide an association between the ModelForm and a model
        model = models.ProformaBillItem
        fields = ('sku', 'name', 'description', 'qty', 'unit_cost',
                  'unit_price')


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
    proforma_bill = forms.ModelChoiceField(
        queryset=models.ProformaBill.objects,
        widget=forms.HiddenInput())

    # An inline class to provide additional information on the form.
    class Meta:
        # Provide an association between the ModelForm and a model
        model = models.ProformaBillItem
        fields = ('sku', 'name', 'description', 'qty', 'unit_cost',
                  'unit_price')
