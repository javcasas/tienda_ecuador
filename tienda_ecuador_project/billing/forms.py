from django import forms
from billing.models import Item, Customer, Bill, BillItem

class ItemForm(forms.ModelForm):
    sku = forms.CharField(max_length=50, help_text="Please enter the SKU.")
    name = forms.CharField(max_length=50, help_text="Please enter the name of the item.")
    description = forms.CharField(max_length=500, help_text="Please enter the description.")

    # An inline class to provide additional information on the form.
    class Meta:
        # Provide an association between the ModelForm and a model
        model = Item
        fields = ('sku', 'name', 'description',)


class BillForm(forms.ModelForm):
    issued_to = forms.ModelChoiceField(queryset=Customer.objects.all(), help_text="Please select the customer.")
    number = forms.CharField(max_length=50, help_text="Please enter the number of the bill.")

    # An inline class to provide additional information on the form.
    class Meta:
        # Provide an association between the ModelForm and a model
        model = Bill
        fields = ('issued_to', 'number')

class BillItemForm(forms.ModelForm):
    sku = forms.CharField(max_length=50, help_text="Please enter the SKU.")
    name = forms.CharField(max_length=50, help_text="Please enter the name of the item.")
    description = forms.CharField(max_length=500, help_text="Please enter the description.")
    qty = forms.IntegerField(help_text='Please enter the quantity')

    # An inline class to provide additional information on the form.
    class Meta:
        # Provide an association between the ModelForm and a model
        model = BillItem
        fields = ('sku', 'name', 'description', 'qty')
