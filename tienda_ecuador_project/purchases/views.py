from datetime import date, timedelta
import pytz
import json
import xml.etree.ElementTree as ET

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.generic import View
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, UpdateView, FormView
from django.core.urlresolvers import reverse
from django.db.models import Count

import models
import forms
from util import signature
from sri.models import AmbienteSRI
import company_accounts.views
import stakeholders.models


tz = pytz.timezone('America/Guayaquil')


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
        print tree
        seller = stakeholders.models.Seller.objects.get_or_create(
            razon_social=tree.find("infoTributaria/razonSocial").text,
            identificacion=tree.find("infoTributaria/ruc").text,
            company=self.company,
            email="")
        purchase = models.Purchase(
            date=tree.find("infoFactura/fechaEmision").text,
            xml_content=form.cleaned_data['xml_content_text'],
            seller=seller,
            closed=False,
            comment="",
            number="{}-{}-{}".format(
                tree.find("infoTributaria/estab").text,
                tree.find("infoTributaria/ptoEmi").text,
                tree.find("infoTributaria/secuencial").text,
            ))
        return super(PurchaseCreateFromXMLView, self).form_valid(form)    


class PurchaseGenerateRetentionView(View):
    pass


class PurchaseAddItemsToInventoryView(View):
    pass


class PurchaseFinishView(View):
    pass
