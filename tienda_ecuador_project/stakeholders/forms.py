# -*- coding: utf-8 -*-
from django import forms
from stakeholders import models


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
        required=False,
        help_text="Por favor teclee el email.")
    direccion = forms.CharField(
        label="Dirección",
        max_length=50,
        required=False,
        help_text="Por favor teclee la dirección.")

    # An inline class to provide additional information on the form.
    class Meta:
        # Provide an association between the ModelForm and a model
        model = models.Customer
        fields = ('razon_social', 'tipo_identificacion',
                  'identificacion', 'email', 'direccion')
