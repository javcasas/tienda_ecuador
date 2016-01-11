from datetime import date, timedelta
import pytz
from decimal import Decimal
import xml.etree.ElementTree as ET

from django.shortcuts import get_object_or_404, redirect
from django.views.generic import View
from django.views.generic.detail import DetailView
from django.views.generic.edit import FormView
from django.core.urlresolvers import reverse
from django.views.generic.list import ListView
from django.db import transaction
from django.views.generic.dates import (YearArchiveView,
                                        MonthArchiveView,
                                        DayArchiveView)
from util.custom_calendar import first_day_of_next_month

import models
import forms
import sri.models
import company_accounts.views
import stakeholders.models
import inventory.models


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


class PurchasesMainMenuView(company_accounts.views.CompanyView,
                            company_accounts.views.CompanySelected,
                            DetailView):
    template_name = 'purchases/purchases_main_menu.html'


class PurchaseCreateFromXMLView(company_accounts.views.CompanySelected,
                                FormView):
    template_name = 'purchases/purchase_create_from_xml.html'
    form_class = forms.PurchaseCreateFromXMLForm

    def get_form(self, form_class=None):
        form = super(PurchaseCreateFromXMLView, self).get_form(form_class)
        # Provide the current company so it can be checked against
        form.company = self.company
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
                seller=seller,
                number="{}-{}-{}".format(
                    tree.find("infoTributaria/estab").text,
                    tree.find("infoTributaria/ptoEmi").text,
                    tree.find("infoTributaria/secuencial").text,
                ),
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
        tree = ET.fromstring(self.purchase.xml_content)
        res['xml'] = tree
        res['detalles'] = tree_to_dict(tree.find('detalles'))
        res['establecimientos'] = (company_accounts.models.Establecimiento
                                   .objects.filter(company=self.company))
        return res

    def post(self, request, **kwargs):
        tree = ET.fromstring(self.purchase.xml_content)
        detalles = tree_to_dict(tree.find('detalles'))
        info_factura = tree_to_dict(tree.find('infoFactura'))

        establecimiento = (company_accounts.models.Establecimiento
                           .objects.filter(company=self.company)
                                   .get(id=request.POST['establecimiento']))
        with transaction.atomic():
            for i, detalle in enumerate(detalles):
                action = request.POST['action-{}'.format(i)]
                if action == 'noop':
                    pass
                elif action == 'create':
                    for decimales_qty in range(0, 3):
                        if (Decimal(detalle['cantidad']) * 10 ** decimales_qty) % 1 == 0:
                            break
                    else:
                        decimales_qty = 3

                    code = (detalle['codigoPrincipal'].strip() or
                            detalle['codigoAuxiliar'].strip() or
                            str(hash(detalle['descripcion']) % 10000000))
                    item, created = inventory.models.Item.objects.get_or_create(
                        company=self.company,
                        name=detalle['descripcion'],
                        description='',
                        tipo=inventory.models.ItemTipo.options.producto,
                        decimales_qty=decimales_qty,
                        distributor_code=detalle['codigoPrincipal'],
                        code=code)
                    for impuesto in detalle['impuestos']:
                        if impuesto['codigo'] == '2':
                            iva = sri.models.Iva.objects.get(
                                codigo=impuesto['codigoPorcentaje'],
                                porcentaje=Decimal(impuesto['tarifa']))
                            item.tax_items.add(iva)
                        elif impuesto['codigo'] == '3':
                            ice = sri.models.Ice.objects.get(
                                codigo=impuesto['codigoPorcentaje'],
                                porcentaje=Decimal(impuesto['tarifa']))
                            item.tax_items.add(ice)
                        else:
                            raise Exception("Codigo de impuesto desconocido: {}"
                                            .format(impuesto['codigo']))

                    d, m, y = info_factura['fechaEmision'].split("/")
                    batch, created = inventory.models.Batch.objects.get_or_create(
                        item=item,
                        unit_cost=Decimal(detalle['precioUnitario']),
                        code=1,
                        acquisition_date=date(int(y), int(m), int(d)),
                        purchase=self.purchase)

                    sku, created = inventory.models.SKU.objects.get_or_create(
                        batch=batch,
                        qty=Decimal(detalle['cantidad']),
                        unit_price=2 * batch.unit_cost,
                        establecimiento=establecimiento,
                        location=' ')
                    print i, 'CREATE'
                elif action == 'add':
                    item_id = request.POST['selected-item-{}'.format(i)]
                    if not item_id:
                        return self.get(request, **kwargs)
                    item = (inventory.models.Item
                            .objects.filter(company=self.company).get(id=item_id))
                    d, m, y = info_factura['fechaEmision'].split("/")
                    curr_code = max([i.code for i in (inventory.models.Batch
                                                      .objects.filter(item=item))] +
                                    [0])
                    batch, created = inventory.models.Batch.objects.get_or_create(
                        item=item,
                        unit_cost=Decimal(detalle['precioUnitario']),
                        code=curr_code + 1,
                        acquisition_date=date(int(y), int(m), int(d)),
                        purchase=self.purchase)

                    sku, created = inventory.models.SKU.objects.get_or_create(
                        batch=batch,
                        qty=Decimal(detalle['cantidad']),
                        unit_price=2 * batch.unit_cost,
                        establecimiento=establecimiento,
                        location=' ')
                    print i, 'ADD', item
                else:
                    raise Exception("Unknown action")
            purchase = self.purchase
            purchase.closed = True
            purchase.save()
            return redirect("purchase_detail", purchase.id)


class PurchaseFinishView(View):
    pass


class PurchaseYearView(PurchaseView,
                       company_accounts.views.CompanySelected,
                       YearArchiveView):
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


class PurchaseMonthView(PurchaseView,
                        company_accounts.views.CompanySelected,
                        MonthArchiveView):
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


class PurchaseDayView(PurchaseView,
                      company_accounts.views.CompanySelected,
                      DayArchiveView):
    date_field = 'date'
    make_object_list = True
    allow_empty = True

    def get_context_data(self, **kwargs):
        context = super(PurchaseDayView, self).get_context_data(**kwargs)
        print context.keys()
        return context
