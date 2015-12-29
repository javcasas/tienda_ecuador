from datetime import date, timedelta
import pytz
import json
from decimal import Decimal
import xml.etree.ElementTree as ET

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.generic import View
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, UpdateView, FormView
from django.core.urlresolvers import reverse
from django.db.models import Count
from django.views.generic.list import ListView

import models
import forms
from util import signature
from sri.models import AmbienteSRI
import company_accounts.views
import stakeholders.models


tz = pytz.timezone('America/Guayaquil')

class PurchaseSelected(company_accounts.views.CompanySelected):
    @property
    def purchase(self):
        return get_object_or_404(
            models.Purchase,
            id=self.purchase_id)

    @property
    def purchase_id(self):
        return self.kwargs['purchase_id']

    @property
    def company_id(self):
        return self.purchase.seller.company.id

    def get_context_data(self, **kwargs):
        context = super(PurchaseSelected, self).get_context_data(**kwargs)
        context['purchase'] = self.purchase
        return context

class PurchaseView(object):
    """
    Base class for an Item View
    """
    model = models.Purchase
    context_object_name = 'purchase'

    def get_queryset(self):
        return self.model.objects.filter(seller__company=self.company)

    @property
    def purchase_id(self):
        return self.model.objects.get(id=self.kwargs['pk']).id


class PurchasesMainMenuView(company_accounts.views.CompanyView, company_accounts.views.CompanySelected, DetailView):
    template_name = 'purchases/purchases_main_menu.html'


class PurchaseCreateFromXMLView(company_accounts.views.CompanySelected, FormView):
    template_name = 'purchases/purchase_create_from_xml.html'
    form_class = forms.PurchaseCreateFromXMLForm
    def get_form(self, form_class=None):
        form = super(PurchaseCreateFromXMLView, self).get_form(form_class)
        form.company = self.company  # Provide the current company so it can be checked against
        return form

    def form_valid(self, form):
        tree = ET.fromstring(form.cleaned_data['xml_content_text'])
        try:
            seller = stakeholders.models.Seller.objects.get(
                razon_social=tree.find("infoTributaria/razonSocial").text,
                identificacion=tree.find("infoTributaria/ruc").text,
                company=self.company)
            seller.nombre_comercial = tree.find("infoTributaria/nombreComercial").text
            seller.save()
        except stakeholders.models.Seller.DoesNotExist:
            seller = stakeholders.models.Seller(
                razon_social=tree.find("infoTributaria/razonSocial").text,
                identificacion=tree.find("infoTributaria/ruc").text,
                company=self.company,
                nombre_comercial=tree.find("infoTributaria/nombreComercial").text)
            seller.save()
                
        dt = tree.find("infoFactura/fechaEmision").text
        d, m, y = dt.split("/")
        try:
            purchase = models.Purchase.objects.get(
                xml_content=form.cleaned_data['xml_content_text'],
            )
        except models.Purchase.DoesNotExist:
            purchase = models.Purchase(
                date="{}-{}-{}".format(y, m, d),
                xml_content=form.cleaned_data['xml_content_text'],
                seller=seller,
                closed=False,
                comment="",
                number="{}-{}-{}".format(
                    tree.find("infoTributaria/estab").text,
                    tree.find("infoTributaria/ptoEmi").text,
                    tree.find("infoTributaria/secuencial").text,
                ),
                total=Decimal(tree.find("infoFactura/importeTotal").text))
            purchase.save()
        self.success_url = reverse("purchase_detail", args=(purchase.id,))
        return super(PurchaseCreateFromXMLView, self).form_valid(form)    


class PurchaseListView(PurchaseView, company_accounts.views.CompanySelected, ListView):
    context_object_name = 'purchase_list'


class PurchaseDetailView(PurchaseView, PurchaseSelected, DetailView):
    pass

class PurchaseGenerateRetentionView(View):
    pass


class PurchaseAddItemsToInventoryView(PurchaseView, PurchaseSelected, DetailView):
    template_name_suffix = '_add_items_to_inventory'

    def get_context_data(self, **kwargs):
        res = super(PurchaseAddItemsToInventoryView, self).get_context_data(**kwargs)
        tree = ET.fromstring(res['purchase'].xml_content)
        res['xml'] = tree
        def tree_to_dict(tree):
            items = tree.getchildren()
            tags = {item.tag for item in items}
            if len(tags) == 0:
                return tree.text
            elif len(tags) == 1:
                return [tree_to_dict(item) for item in items]
            elif len(tags) == len(items):
                return {item.tag: tree_to_dict(item) for item in items}
            else:
                raise Exception("Error on {}".format(tree))
            
        res['detalles'] = tree_to_dict(tree.find('detalles'))
        res['establecimientos'] = company_accounts.models.Establecimiento.objects.filter(company=self.company)
            
        return res


class PurchaseFinishView(View):
    pass

from django.views.generic.dates import YearArchiveView, MonthArchiveView, DayArchiveView
from util.custom_calendar import first_day_of_next_month


class PurchaseYearView(PurchaseView, company_accounts.views.CompanySelected, YearArchiveView):
    date_field = 'date'
    make_object_list = True
    allow_empty = True

    def get_context_data(self, **kwargs):
        context = super(PurchaseYearView, self).get_context_data(**kwargs)
        context['date_content'] = []
        for dt in context['date_list']:
            check = {
                self.date_field + "__gte": dt,
                self.date_field + "__lt": first_day_of_next_month(dt),
            }
            items = context['object_list'].filter(**check)
            total = sum(map(lambda x: x.total, items), Decimal(0))
            context['date_content'].append((dt, items, total))
        return context


class PurchaseMonthView(PurchaseView, company_accounts.views.CompanySelected, MonthArchiveView):
    date_field = 'date'
    make_object_list = True
    allow_empty = True

    def get_context_data(self, **kwargs):
        context = super(PurchaseMonthView, self).get_context_data(**kwargs)
        context['date_content'] = []
        for dt in context['date_list']:
            check = {
                self.date_field + "__gte": dt,
                self.date_field + "__lt": dt + timedelta(days=1),
            }
            items = context['object_list'].filter(**check)
            total = sum(map(lambda x: x.total, items), Decimal(0))
            context['date_content'].append((dt, items, total))
        return context


class PurchaseDayView(PurchaseView, company_accounts.views.CompanySelected, DayArchiveView):
    date_field = 'date'
    make_object_list = True
    allow_empty = True
    def get_context_data(self, **kwargs):
        context = super(PurchaseDayView, self).get_context_data(**kwargs)
        print context.keys()
        return context
