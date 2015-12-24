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
from company_accounts.views import CompanyView, CompanySelected, LicenceControlMixin, EstablecimientoSelected

tz = pytz.timezone('America/Guayaquil')


class CompanyProfileView(CompanyView, CompanySelected, DetailView):
    """
    View that shows a general index for a given company
    """

####################################################################
#   Item views
####################################################################
class ItemView(object):
    """
    Base class for an Item View
    """
    model = models.Item
    context_object_name = 'item'

    def get_queryset(self):
        return self.model.objects.filter(company=self.company)

    @property
    def company_id(self):
        return self.model.objects.get(id=self.kwargs['pk']).company.id


class ItemListView(CompanySelected, ItemView, ListView):
    """
    View that shows the items for the current company
    """
    context_object_name = "item_list"


#class ItemListViewJson(JSONResponseMixin, ItemListView):
#    def render_to_response(self, context, **response_kwargs):
#        return self.render_to_json_response(context, **response_kwargs)


class ItemDetailView(ItemView, CompanySelected, DetailView):
    """
    Detail view for Items
    """


class ItemCreateView(CompanySelected, ItemView, CreateView):
    """
    Create view for items
    """
    template_name_suffix = '_create_form'
    form_class = forms.ItemForm

    def get_form(self, *args):
        res = super(ItemCreateView, self).get_form(*args)
        return res

    def form_valid(self, form):
        form.instance.company = self.company
        form.instance.save()
        item = models.Item.objects.get(id=form.instance.id)
        if form.data['ice']:
            item.tax_items.add(models.Ice.objects.get(pk=form.data['ice']))
        item.tax_items.add(models.Iva.objects.get(pk=form.data['iva']))
        return super(ItemCreateView, self).form_valid(form)


class ItemUpdateView(ItemView, CompanySelected, UpdateView):
    form_class = forms.ItemForm

    def get_form(self, *args, **kwargs):
        form = super(ItemUpdateView, self).get_form(*args, **kwargs)
        item = models.Item.objects.get(pk=self.kwargs['pk'])
        form.fields['iva'].initial = item.iva
        form.fields['ice'].initial = item.ice
        return form

    def form_valid(self, form):
        item = models.Item.objects.get(id=form.instance.id)
        for ti in item.tax_items.all():
            item.tax_items.remove(ti)
        if form.data['ice']:
            item.tax_items.add(models.Ice.objects.get(pk=form.data['ice']))
        item.tax_items.add(models.Iva.objects.get(pk=form.data['iva']))
        return super(ItemUpdateView, self).form_valid(form)


class ItemDeleteView(ItemView, CompanySelected, DeleteView):
    @property
    def success_url(self):
        return reverse("item_index", args=(self.company.id, ))


class ItemSelected(CompanySelected):
    @property
    def item(self):
        return get_object_or_404(
            models.Item,
            id=self.item_id)

    @property
    def item_id(self):
        return self.kwargs['item_id']

    @property
    def company_id(self):
        return self.item.company.id

    def get_context_data(self, **kwargs):
        context = super(ItemSelected, self).get_context_data(**kwargs)
        context['item'] = self.item
        return context

####################################################################
#   Batch views
####################################################################
class BatchView(object):
    """
    Base class for an Item View
    """
    model = models.Batch
    context_object_name = 'batch'

    def get_queryset(self):
        return self.model.objects.filter(item=self.item)

    @property
    def item_id(self):
        return self.model.objects.get(id=self.kwargs['pk']).item.id


class BatchListView(ItemSelected, BatchView, ListView):
    """
    View that shows the items for the current company
    """
    context_object_name = "batch_list"


#class ItemListViewJson(JSONResponseMixin, ItemListView):
#    def render_to_response(self, context, **response_kwargs):
#        return self.render_to_json_response(context, **response_kwargs)


class BatchDetailView(BatchView, ItemSelected, DetailView):
    """
    Detail view for Items
    """


class BatchCreateView(ItemSelected, BatchView, CreateView):
    """
    Create view for items
    """
    template_name_suffix = '_create_form'
    #form_class = forms.ItemForm

    def form_valid(self, form):
        form.instance.item = self.item
        return super(BatchCreateView, self).form_valid(form)


class BatchUpdateView(BatchView, ItemSelected, UpdateView):
    """
    """
    #form_class = forms.ItemForm


class BatchDeleteView(BatchView, ItemSelected, DeleteView):
    @property
    def success_url(self):
        return reverse("batch_index", args=(self.item.id, ))

class BatchSelected(ItemSelected):
    @property
    def batch(self):
        return get_object_or_404(
            models.Batch,
            id=self.batch_id)

    @property
    def batch_id(self):
        return self.kwargs['batch_id']

    @property
    def item_id(self):
        return self.batch.item.id

    def get_context_data(self, **kwargs):
        context = super(BatchSelected, self).get_context_data(**kwargs)
        context['batch'] = self.batch
        return context


####################################################################
#   SKU views
####################################################################
class SKUView(object):
    """
    Base class for an Item View
    """
    model = models.SKU
    context_object_name = 'sku'

    def get_queryset(self):
        return self.model.objects.filter(batch=self.batch)

    @property
    def batch_id(self):
        return self.model.objects.get(id=self.kwargs['pk']).batch.id


class SKUEstablecimientoListView(EstablecimientoSelected, SKUView, ListView):
    """
    View that shows the items for the current company
    """
    context_object_name = "sku_list"
    template_name_suffix = '_establecimiento_list'

    def get_queryset(self):
        return self.model.objects.filter(establecimiento=self.establecimiento)


#class ItemListViewJson(JSONResponseMixin, ItemListView):
#    def render_to_response(self, context, **response_kwargs):
#        return self.render_to_json_response(context, **response_kwargs)


class SKUDetailView(SKUView, BatchSelected, DetailView):
    """
    Detail view for Items
    """


class SKUCreateView(BatchSelected, SKUView, CreateView):
    """
    Create view for items
    """
    template_name_suffix = '_create_form'
    #form_class = forms.ItemForm

    def form_valid(self, form):
        form.instance.batch = self.batch
        return super(SKUCreateView, self).form_valid(form)


class SKUUpdateView(SKUView, BatchSelected, UpdateView):
    """
    """
    #form_class = forms.ItemForm


class SKUDeleteView(SKUView, BatchSelected, DeleteView):
    @property
    def success_url(self):
        return reverse("sku_index", args=(self.batch.id, ))
