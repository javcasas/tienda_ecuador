# -*- coding: utf-8 -*-
from datetime import date
from django import forms
import models
import sri.models as sri


class ItemForm(forms.ModelForm):
    name = forms.CharField(
        label='Nombre',
        max_length=50,
        help_text="Por favor teclee el nombre del artículo.")
    code = forms.CharField(
        label='Código',
        max_length=50,
        help_text="Por favor teclee un código para el artículo.")
    tipo = forms.ChoiceField(
        label='Tipo',
        choices=models.ItemTipo.__OPTIONS__,
        help_text="Por favor seleccione el tipo del artículo.")
    decimales_qty = forms.ChoiceField(
        label='Decimales en cantidad',
        choices=models.ItemDecimales.__OPTIONS__)
    description = forms.CharField(
        label="Descripción",
        max_length=500,
        widget=forms.Textarea(),
        required=False,
        help_text="Por favor teclee una descripción.")
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
        fields = ('name', 'code', 'iva', 'ice', 'tipo', 'description',
                  'decimales_qty')

    def clean(self):
        cleaned_data = super(ItemForm, self).clean()
        # Check unique constraint
        try:
            self.Meta.model.objects.get(company=self.instance.company,
                                        code=cleaned_data['code'])
            self.add_error('code',
                           u'Código repetido, por favor utilice otro código.')
        except self.Meta.model.DoesNotExist:
            pass
        return cleaned_data


class BatchForm(forms.ModelForm):
    code = forms.CharField(
        label='Código',
        max_length=50,
        help_text="Por favor teclee un código para el artículo.")
    unit_cost = forms.DecimalField(
        label='Coste',
        decimal_places=4)
    date = forms.DateField(
        initial=date.today,
        label='Fecha')

    # An inline class to provide additional information on the form.
    class Meta:
        # Provide an association between the ModelForm and a model
        model = models.Batch
        fields = ('code', 'unit_cost', 'date',)

    def clean(self):
        cleaned_data = super(BatchForm, self).clean()
        # Check unique constraint
        try:
            self.Meta.model.objects.get(item=self.instance.item,
                                        code=cleaned_data['code'])
            self.add_error('code',
                           u'Código repetido, por favor utilice otro código.')
        except self.Meta.model.DoesNotExist:
            pass
        return cleaned_data


class SKUForm(forms.ModelForm):
    unit_price = forms.DecimalField(
        label='Precio',
        decimal_places=4)
    qty = forms.DecimalField(
        label='Cantidad',
        decimal_places=4)
    establecimiento = forms.ModelChoiceField(
        label='Establecimiento',
        queryset=None,
        help_text=u'Seleccione el establecimiento en el que está localizada la mercadería')

    # An inline class to provide additional information on the form.
    class Meta:
        # Provide an association between the ModelForm and a model
        model = models.Item
        fields = ('unit_price', 'qty',)

    def clean(self):
        cleaned_data = super(SKUForm, self).clean()
        # Check unique constraint
        try:
            self.Meta.model.objects.get(item=self.instance.item,
                                        code=cleaned_data['code'])
            self.add_error('code',
                           u'Código repetido, por favor utilice otro código.')
        except self.Meta.model.DoesNotExist:
            pass
        return cleaned_data
