# -*- coding: utf-8 -*-
from datetime import date
from django import forms
import models
import sri.models as sri
from decimal import Decimal
from util.forms import UpdatedDecimalField


class ItemForm(forms.ModelForm):
    name = forms.CharField(
        label='Nombre',
        max_length=50,
        help_text="La denominación artículo.")
    code = forms.CharField(
        label='Código',
        max_length=50,
        help_text="Código asignado al artículo.")
    tipo = forms.ChoiceField(
        label='Tipo',
        choices=models.ItemTipo.__OPTIONS__,
        help_text="Si el artículo es un producto o un servicio.")
    decimales_qty = forms.ChoiceField(
        label='Decimales en cantidad',
        choices=models.ItemDecimales.__OPTIONS__)
    description = forms.CharField(
        label="Descripción",
        max_length=500,
        widget=forms.Textarea(),
        required=False,
        help_text="Descripción del artículo")
    iva = forms.ModelChoiceField(
        label='IVA',
        queryset=sri.Iva.objects,
        help_text='Tipo de IVA del artículo')
    ice = forms.ModelChoiceField(
        label='ICE',
        queryset=sri.Ice.objects,
        required=False,
        empty_label='Sin ICE',
        help_text='Tipo de ICE del artículo')

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
            ob = self.Meta.model.objects.get(
                company=self.instance.company,
                code=cleaned_data['code'])
            if self.instance.id != ob.id:
                self.add_error('code',
                               u'Código repetido, por favor utilice otro código.')
        except self.Meta.model.DoesNotExist:
            pass
        return cleaned_data


class BatchForm(forms.ModelForm):
    code = forms.IntegerField(
        label=u'Código',
        help_text=u"Código para distinguir a este lote de otros lotes del mismo artículo.")
    unit_cost = UpdatedDecimalField(
        label='Coste',
        help_text=u"Coste de referencia de cada artículo en este lote.",
        decimal_places=4)
    acquisition_date = forms.DateField(
        initial=date.today,
        help_text=u"Fecha de adquisición del lote.",
        label=u'Fecha de Adquisición')

    # An inline class to provide additional information on the form.
    class Meta:
        # Provide an association between the ModelForm and a model
        model = models.Batch
        fields = ('code', 'unit_cost', 'acquisition_date')

    def clean(self):
        cleaned_data = super(BatchForm, self).clean()
        # Check unique constraint
        try:
            ob = self.Meta.model.objects.get(
                item=self.instance.item,
                code=cleaned_data['code'])
            if self.instance.id != ob.id:
                self.add_error('code',
                               u'Código repetido, por favor utilice otro código.')
        except self.Meta.model.DoesNotExist:
            pass
        return cleaned_data


class SKUForm(forms.ModelForm):
    unit_price = UpdatedDecimalField(
        label='Precio de venta',
        help_text=u'El precio de referencia al que se venderá en el establecimiento',
        decimal_places=4)
    qty = UpdatedDecimalField(
        label='Cantidad',
        help_text=u'La cantidad que hay almacenada en el establecimiento',
        decimal_places=4)
    qty_unlimited = forms.BooleanField(
        label='Inventario ilimitado',
        required=False,
        help_text=u'El artículo es un servicio y no hay límite en la cantidad que se puede vender')
    establecimiento = forms.ModelChoiceField(
        label='Establecimiento',
        queryset=None,
        help_text=u'El establecimiento en el que está localizada la mercadería')

    # An inline class to provide additional information on the form.
    class Meta:
        # Provide an association between the ModelForm and a model
        model = models.SKU
        fields = ('unit_price', 'qty_unlimited', 'qty', 'establecimiento',)

    def clean(self):
        cleaned_data = super(SKUForm, self).clean()
        # Check unique constraint
        try:
            ob = self.Meta.model.objects.get(batch=self.instance.batch,
                                             establecimiento=cleaned_data['establecimiento'])
            if self.instance.id != ob.id:
                self.add_error('establecimiento',
                               u'Ya hay un inventario en ese establecimiento.')
        except self.Meta.model.DoesNotExist:
            pass
        return cleaned_data


class SmartModelChoiceField(forms.ModelChoiceField):
    def __init__(self, *args, **kwargs):
        res = super(SmartModelChoiceField, self).__init__(*args, **kwargs)
        self._saved_widget = self.widget
        self._saved_initial = self.initial
        return res

    def _set_queryset(self, queryset):
        if queryset and len(queryset) == 1:
            self.widget = forms.HiddenInput()
            self.initial = queryset[0]
        else:
            try:
                self.widget = self._saved_widget
                self.initial = self._saved_initial
            except AttributeError:
                # During __init__
                pass
        return super(SmartModelChoiceField, self)._set_queryset(queryset)

    queryset = property(forms.ModelChoiceField._get_queryset, _set_queryset)


class ItemBatchSKUForm(forms.ModelForm):
    name = forms.CharField(
        label=u'Nombre',
        max_length=50,
        help_text=u"La denominación del artículo.")
    code = forms.CharField(
        label=u'Código',
        max_length=50,
        help_text=u"Código asignado al artículo.")
    tipo = forms.ChoiceField(
        label='Tipo',
        choices=models.ItemTipo.__OPTIONS__,
        widget=forms.HiddenInput(),
        initial=models.ItemTipo.options.producto,
        help_text="Si el artículo es un producto o un servicio.")
    decimales_qty = forms.ChoiceField(
        label='Decimales en cantidad',
        choices=models.ItemDecimales.__OPTIONS__)
    description = forms.CharField(
        label=u"Descripción",
        max_length=500,
        widget=forms.Textarea(),
        required=False)
    iva = forms.ModelChoiceField(
        label='IVA',
        queryset=sri.Iva.objects,
        help_text='Tipo de IVA del artículo')
    ice = forms.ModelChoiceField(
        label='ICE',
        queryset=sri.Ice.objects,
        required=False,
        empty_label='Sin ICE',
        help_text='Tipo de ICE del artículo')
    unit_cost = UpdatedDecimalField(
        label='Coste',
        help_text=u"Coste de referencia del artículo.",
        decimal_places=4)
    acquisition_date = forms.DateField(
        initial=date.today,
        help_text=u"Fecha de adquisición del artículo.",
        label=u'Fecha de Adquisición')
    unit_price = UpdatedDecimalField(
        label='Precio de venta',
        help_text=u'El precio de referencia al que se venderá en el establecimiento',
        decimal_places=4)
    qty_unlimited = forms.BooleanField(
        widget=forms.HiddenInput(),
        required=False,
        initial=False)
    qty = UpdatedDecimalField(
        label='Cantidad',
        help_text=u'La cantidad que hay almacenada en el establecimiento',
        decimal_places=4)
    establecimiento = SmartModelChoiceField(
        label='Establecimiento',
        queryset=None,
        help_text=u'El establecimiento en el que está localizada la mercadería')

    # An inline class to provide additional information on the form.
    class Meta:
        # Provide an association between the ModelForm and a model
        model = models.SKU
        fields = (('unit_price', 'qty', 'establecimiento',) +
                  ('name', 'code', 'iva', 'ice', 'tipo', 'description',
                   'decimales_qty') +
                  ('code', 'unit_cost', 'acquisition_date'))


class ServiceBatchSKUForm(ItemBatchSKUForm):
    # Newly hidden fields
    tipo = forms.ChoiceField(
        choices=models.ItemTipo.__OPTIONS__,
        widget=forms.HiddenInput(),
        initial=models.ItemTipo.options.servicio)
    qty = UpdatedDecimalField(
        widget=forms.HiddenInput(),
        initial=10000000,
        decimal_places=4)
    qty_unlimited = forms.BooleanField(
        widget=forms.HiddenInput(),
        required=False,
        initial=True)
    unit_cost = UpdatedDecimalField(
        widget=forms.HiddenInput(),
        initial=Decimal(0),
        decimal_places=4)
    acquisition_date = forms.DateField(
        initial=date.today,
        widget=forms.HiddenInput())
    decimales_qty = forms.ChoiceField(
        widget=forms.HiddenInput(),
        initial=0,
        choices=models.ItemDecimales.__OPTIONS__)

    # Same fields with different data
    name = forms.CharField(
        label='Nombre',
        max_length=50,
        help_text=u"La denominación del Servicio.")
    code = forms.CharField(
        label='Código',
        max_length=50,
        help_text=u"Código asignado al Servicio.")
    establecimiento = SmartModelChoiceField(
        label='Establecimiento',
        queryset=None,
        help_text=u'El establecimiento donde se venderá el servicio')
