import tempfile
import os
import base64
import pytz
from datetime import datetime, timedelta

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.generic import View
from django.views.generic.list import ListView
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.core.urlresolvers import reverse
from django.http import JsonResponse
from django.forms.models import model_to_dict

import models
import forms
import billing.models
from company_accounts.views import CompanyView, CompanySelected

tz = pytz.timezone('America/Guayaquil')


class CompanyIndexView(CompanyView,
                       CompanySelected,
                       ListView):
    """
    View that shows a general index for a given company
    """
    template_name = 'accounts_receivable/company_index.html'
    model = models.Receivable
    context_object_name = 'receivable_list'
    received = False

    def get_queryset(self):
        return self.model.objects.filter(bill__company=self.company, received=self.received)


class ReceivableView(object):
    model = models.Receivable
    context_object_name = 'receivable'

    @property
    def company_id(self):
        return self.get_object().bill.company.id


class ReceivableDetailView(ReceivableView, CompanySelected, DetailView):
    """
    """

class ReceivableUpdateView(ReceivableView, CompanySelected, UpdateView):
    """
    """
    form_class = forms.ReceivableForm

class ReceivableConfirmReceivedView(ReceivableView, CompanySelected, DetailView):
    """
    """
    template_name_suffix = '_confirm_received'
    def post(self, request, pk):
        r = self.get_object()
        r.received = True
        r.save()
        return redirect("receivable_detail", r.id)

class ReceivableSelected(CompanySelected):
    @property
    def receivable(self):
        return get_object_or_404(
            models.Receivable,
            id=self.receivable_id)

    @property
    def receivable_id(self):
        return self.kwargs['receivable_id']

    @property
    def company_id(self):
        return self.receivable.bill.company.id

    def get_context_data(self, **kwargs):
        context = super(ReceivableSelected, self).get_context_data(**kwargs)
        context['receivable'] = self.receivable
        return context

class PaymentCreateView(ReceivableSelected, CreateView):
    """
    """
    model = models.Payment
    context_object_name = 'payment'
    form_class = forms.PaymentForm

    def get_form(self, *args):
        form = super(PaymentCreateView, self).get_form(*args)
        form.fields['qty'].initial = self.receivable.amount_left
        return form

    def form_valid(self, form):
        form.instance.receivable = self.receivable
        return super(PaymentCreateView, self).form_valid(form)

    @property
    def success_url(self):
        if self.receivable.amount_left <= 0:
            print "ASDFASDFASD"
            return reverse("receivable_confirm_received", args=(self.receivable.id,))
        else:
            print "asdfasdfasd"
            return reverse("receivable_detail", args=(self.receivable.id,))
