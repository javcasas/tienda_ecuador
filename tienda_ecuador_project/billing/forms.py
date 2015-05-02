from django import forms
from billing.models import Item

class ItemForm(forms.ModelForm):
    sku = forms.CharField(max_length=50, help_text="Please enter the SKU.")
    name = forms.CharField(max_length=50, help_text="Please enter the name of the item.")
    description = forms.CharField(max_length=500, help_text="Please enter the description.")

    # An inline class to provide additional information on the form.
    class Meta:
        # Provide an association between the ModelForm and a model
        model = Item
        fields = ('sku', 'name', 'description',)
