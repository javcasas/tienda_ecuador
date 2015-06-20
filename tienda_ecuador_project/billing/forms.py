from datetime import datetime
from django import forms
from billing.models import Item, Customer, ProformaBill, ProformaBillItem, Company, Bill, BillItem, Iva, Ice


class ItemForm(forms.ModelForm):
    sku = forms.CharField(max_length=50, help_text="Please enter the SKU.")
    name = forms.CharField(max_length=50, help_text="Please enter the name of the item.")
    description = forms.CharField(max_length=500, help_text="Please enter the description.")
    iva = forms.ModelChoiceField(queryset=Iva.objects, help_text="Please select the IVA.")
    ice = forms.ModelChoiceField(queryset=Ice.objects, help_text="Please select the ICE.")
    unit_cost = forms.DecimalField(decimal_places=4, help_text="Please enter the unit cost.")
    unit_price = forms.DecimalField(decimal_places=4, help_text="Please enter the unit price.")
    #company = forms.ModelChoiceField(queryset=Company.objects.all(), help_text="Please select the company.")

    # An inline class to provide additional information on the form.
    class Meta:
        # Provide an association between the ModelForm and a model
        model = Item
        fields = ('sku', 'name', 'description', 'iva', 'ice', 'unit_cost', 'unit_price')


class ProformaBillForm(forms.ModelForm):
    issued_to = forms.ModelChoiceField(queryset=None, help_text="Please select the customer.")
    number = forms.CharField(max_length=50, help_text="Please enter the number of the bill.")
    date = forms.DateTimeField(initial=datetime.utcnow, help_text='Please select the date')

    class Meta:
        # Provide an association between the ModelForm and a model
        model = ProformaBill
        fields = ('issued_to', 'number', 'date')


class BillItemForm(forms.ModelForm):
    sku = forms.CharField(max_length=50, help_text="Please enter the SKU.")
    name = forms.CharField(max_length=50, help_text="Please enter the name of the item.")
    description = forms.CharField(max_length=500, help_text="Please enter the description.")
    qty = forms.IntegerField(help_text='Please enter the quantity')
    bill = forms.ModelChoiceField(widget=forms.HiddenInput, queryset=Bill.objects.all(), help_text="Please select the bill.")
    company = forms.ModelChoiceField(widget=forms.HiddenInput, queryset=Company.objects.all(), help_text="Please select the company.")

    # An inline class to provide additional information on the form.
    class Meta:
        # Provide an association between the ModelForm and a model
        model = BillItem
        fields = ('sku', 'name', 'description', 'qty', 'bill', 'company')


class CustomerForm(forms.ModelForm):
    razon_social = forms.CharField(max_length=50, help_text="Por favor teclee la razon social.")
    tipo_identificacion = forms.ChoiceField(choices=[('ruc', 'RUC'), ('cedula', 'Cedula')], help_text="Por favor teclee la razon social.")
    identificacion = forms.CharField(max_length=50, help_text="Por favor teclee la identificacion.")
    email = forms.CharField(max_length=50, help_text="Por favor teclee el email.")
    direccion = forms.CharField(max_length=50, help_text="Por favor teclee la direccion.")

    # An inline class to provide additional information on the form.
    class Meta:
        # Provide an association between the ModelForm and a model
        model = Customer
        fields = ('razon_social', 'tipo_identificacion', 'identificacion', 'email', 'direccion')


class ProformaBillItemForm(forms.ModelForm):
    sku = forms.CharField(max_length=50, help_text="Please enter the SKU.")
    name = forms.CharField(max_length=50, help_text="Please enter the name of the item.")
    description = forms.CharField(max_length=500, help_text="Please enter the description.")
    qty = forms.IntegerField(help_text='Please enter the quantity')
    copy_from = forms.ModelChoiceField(queryset=None, required=False, help_text="Please select the item to copy from.")

    def clean(self):
        cleaned_data = super(ProformaBillItemForm, self).clean()
        data = self.data.copy()
        if 'copy_from' in cleaned_data and cleaned_data['copy_from']:
            copy_from = cleaned_data['copy_from']
            cleaned_data['sku'] = copy_from.sku
            cleaned_data['name'] = copy_from.name
            cleaned_data['description'] = copy_from.description
            data['sku'] = copy_from.sku
            data['name'] = copy_from.name
            data['description'] = copy_from.description
        data['copy_from'] = None
        self.data = data
        return cleaned_data

    def is_valid(self):
        res = super(self.__class__, self).is_valid()
        print self.cleaned_data
        print self.data
        print res
        return res

    # An inline class to provide additional information on the form.
    class Meta:
        # Provide an association between the ModelForm and a model
        model = ProformaBillItem
        fields = ('sku', 'name', 'description', 'qty')
