# * encoding: utf-8 *
import pytz

from django.db.models import Max
from django.shortcuts import get_object_or_404
from django.views.generic.list import ListView
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.core.urlresolvers import reverse
from django.http import JsonResponse
from django.db import transaction
import django.forms

import models
import forms
from company_accounts.views import (CompanyView,
                                    CompanySelected,
                                    EstablecimientoSelected)
import company_accounts.models
from django.forms.models import model_to_dict

import util.json_utils


tz = pytz.timezone('America/Guayaquil')


class JSONResponseMixin(object):
    """
    A mixin that can be used to render a JSON response.
    """
    def render_to_json_response(self, context, **response_kwargs):
        """
        Returns a JSON response, transforming 'context' to make the payload.
        """
        return JsonResponse(
            self.get_data(context),
            safe=False,
            **response_kwargs
        )

    def get_data(self, context):
        """
        Returns an object that will be serialized as JSON by json.dumps().
        """
        # Note: This is *EXTREMELY* naive; in reality, you'll need
        # to do much more complex handling to ensure that arbitrary
        # objects -- such as Django model instances or querysets
        # -- can be serialized as JSON.
        return map(model_to_dict,
                   list(self.model.objects.filter(company=self.company)))


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


class ItemListViewJson(JSONResponseMixin, ItemListView):
    def render_to_response(self, context, **response_kwargs):
        return self.render_to_json_response(context, **response_kwargs)


class ItemDetailView(ItemView, CompanySelected, DetailView):
    """
    Detail view for Items
    """


class ItemCreateView(CompanySelected, ItemView, CreateView):
    """
    Create view for items
    """
    form_class = forms.ItemForm

    def get_form(self, *args):
        res = super(ItemCreateView, self).get_form(*args)
        res.instance.company = self.company
        return res

    def form_valid(self, form):
        res = super(ItemCreateView, self).form_valid(form)
        if form.data['ice']:
            form.instance.tax_items.add(
                models.Ice.objects.get(pk=form.data['ice']))
        form.instance.tax_items.add(
            models.Iva.objects.get(pk=form.data['iva']))
        return res


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
    def get_success_url(self):
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


# class ItemListViewJson(JSONResponseMixin, ItemListView):
#     def render_to_response(self, context, **response_kwargs):
#         return self.render_to_json_response(context, **response_kwargs)


class BatchDetailView(BatchView, ItemSelected, DetailView):
    """
    Detail view for Items
    """


class BatchCreateView(ItemSelected, BatchView, CreateView):
    """
    Create view for items
    """
    form_class = forms.BatchForm

    def get_form(self, **kwargs):
        form = super(BatchCreateView, self).get_form(**kwargs)
        form.fields['code'].initial = (models.Batch.objects
                                       .filter(item=self.item)
                                       .aggregate(Max('code'))['code__max']) or 1
        form.instance.item = self.item
        return form


class BatchUpdateView(BatchView, ItemSelected, UpdateView):
    """
    """
    form_class = forms.BatchForm


class BatchDeleteView(BatchView, ItemSelected, DeleteView):
    def get_success_url(self):
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


class SKUEstablecimientoListJSONView(EstablecimientoSelected,
                                     SKUView,
                                     util.json_utils.ListJSONResponseMixin,
                                     ListView):
    """
    View that shows the items for the current company
    """
    context_object_name = "sku_list"
    template_name_suffix = '_establecimiento_list'
    fields_to_return = ['code', 'name', 'id', 'qty', 'unit_price', 'location']

    def get_queryset(self):
        return self.model.objects.filter(establecimiento=self.establecimiento)


class SKUDetailView(SKUView, BatchSelected, DetailView):
    """
    Detail view for Items
    """


class SKUCreateView(BatchSelected, SKUView, CreateView):
    """
    Create view for items
    """
    form_class = forms.SKUForm

    def get_form(self, **kwargs):
        form = super(SKUCreateView, self).get_form(**kwargs)
        form.fields['establecimiento'].queryset = (company_accounts.models
                                                   .Establecimiento.objects
                                                   .filter(company=self.company))
        form.fields['qty'].decimal_places = self.item.decimales_qty
        form.instance.batch = self.batch
        return form


class SKUUpdateView(SKUView, BatchSelected, UpdateView):
    """
    """
    form_class = forms.SKUForm

    def get_form(self, **kwargs):
        form = super(SKUUpdateView, self).get_form(**kwargs)
        form.fields['establecimiento'].queryset = (company_accounts.models
                                                   .Establecimiento.objects
                                                   .filter(company=self.company))
        form.fields['qty'].decimal_places = self.item.decimales_qty
        form.instance.batch = self.batch
        return form


class SKUDeleteView(SKUView, BatchSelected, DeleteView):
    def get_success_url(self):
        return reverse("sku_index", args=(self.batch.id, ))


# Fast create views
class ItemBatchSKUCreateView(CompanySelected, SKUView, CreateView):
    """
    Create view for items
    """
    form_class = forms.ItemBatchSKUForm
    template_name_suffix = '_batch_item_create_form'

    def get_form(self, *args):
        form = super(ItemBatchSKUCreateView, self).get_form(*args)
        form.instance.company = self.company
        establecimientos = (company_accounts.models
                            .Establecimiento.objects
                            .filter(company=self.company))
        form.fields['establecimiento'].queryset = establecimientos
        form.fields['tipo'].widget = django.forms.HiddenInput()
        form.fields['tipo'].initial = 'producto'
        return form

    def form_valid(self, form):
        with transaction.atomic():
            data = form.cleaned_data
            item, _ = models.Item.objects.get_or_create(
                name=data['name'],
                code=data['code'],
                description=data['description'],
                tipo=data['tipo'],
                decimales_qty=data['decimales_qty'],
                company=self.company)
            if data['ice']:
                item.tax_items.add(data['ice'])
            item.tax_items.add(data['iva'])

            batch, _ = models.Batch.objects.get_or_create(
                item=item,
                unit_cost=data['unit_cost'],
                code=1,
                acquisition_date=data['acquisition_date'])

            form.instance.batch = batch
            res = super(ItemBatchSKUCreateView, self).form_valid(form)
            return res

    def get_context_data(self, **kwargs):
        context = super(ItemBatchSKUCreateView, self).get_context_data(**kwargs)
        context['tipo'] = u'Artículo'
        return context


class ServiceBatchSKUCreateView(ItemBatchSKUCreateView):
    """
    Create view for items
    """
    form_class = forms.ServiceBatchSKUForm
    template_name_suffix = '_batch_item_create_form'

    def get_context_data(self, **kwargs):
        context = super(ServiceBatchSKUCreateView, self).get_context_data(**kwargs)
        context['tipo'] = u'Servicio'
        return context
