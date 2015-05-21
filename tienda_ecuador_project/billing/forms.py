from django import forms
from billing.models import Item, Customer, ProformaBill, ProformaBillItem, Company, Bill, BillItem


class ItemForm(forms.ModelForm):
    sku = forms.CharField(max_length=50, help_text="Please enter the SKU.")
    name = forms.CharField(max_length=50, help_text="Please enter the name of the item.")
    description = forms.CharField(max_length=500, help_text="Please enter the description.")
    #company = forms.ModelChoiceField(queryset=Company.objects.all(), help_text="Please select the company.")

    # An inline class to provide additional information on the form.
    class Meta:
        # Provide an association between the ModelForm and a model
        model = Item
        fields = ('sku', 'name', 'description')


class ProformaBillForm(forms.ModelForm):
    issued_to = forms.ModelChoiceField(queryset=None, help_text="Please select the customer.")
    number = forms.CharField(max_length=50, help_text="Please enter the number of the bill.")

    class Meta:
        # Provide an association between the ModelForm and a model
        model = ProformaBill
        fields = ('issued_to', 'number')


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
    name = forms.CharField(max_length=50, help_text="Please enter the name of the customer.")
    #company = forms.ModelChoiceField(widget=forms.HiddenInput, queryset=Company.objects.all(), help_text="Please select the company.")

    # An inline class to provide additional information on the form.
    class Meta:
        # Provide an association between the ModelForm and a model
        model = Customer
        fields = ('name',)
