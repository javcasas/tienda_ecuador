# -*- coding: utf-8 -*-
import datetime
from django import forms
from accounts_receivable import models
import billing.models
from util.forms import UpdatedDecimalField


class ReceivableForm(forms.ModelForm):
    comment = forms.CharField(
        label='Comentario',
        widget=forms.Textarea(),
        help_text="Por favor teclee un comentario.")
    received = forms.BooleanField(
        label='Cobrado',
        required=False,
        help_text="Marque si la cuenta debe considerarse cobrada.")

    # An inline class to provide additional information on the form.
    class Meta:
        # Provide an association between the ModelForm and a model
        model = models.Receivable
        fields = ('comment', 'received',)


class PaymentForm(forms.ModelForm):
    date = forms.DateField(
        initial=datetime.date.today,
        label='Fecha')
    qty = UpdatedDecimalField(
        label='Cantidad cobrada',
        decimal_places=2,
        min_value=0,
        help_text="Teclee la cantidad cobrada.")
    customer_pays = forms.DecimalField(
        label='Calculadora de Vueltos',
        decimal_places=2,
        min_value=0,
        required=False,
        help_text="Teclee la cantidad que ha entregado el cliente.")
    method = forms.ModelChoiceField(
        label='Forma de pago',
        queryset=billing.models.FormaPago.objects,
        help_text='Por favor, seleccione la forma de pago')
    comment = forms.CharField(
        label='Comentario',
        widget=forms.Textarea(),
        required=False,
        help_text="Por favor teclee un comentario.")

    # An inline class to provide additional information on the form.
    class Meta:
        # Provide an association between the ModelForm and a model
        model = models.Payment
        fields = ('date', 'qty', 'method', 'comment')
