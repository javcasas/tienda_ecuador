import tempfile
import os
import base64
import pytz
import time
from datetime import datetime, timedelta
from decimal import Decimal

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.generic import View
from django.views.generic.list import ListView
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.core.urlresolvers import reverse
from django.http import JsonResponse, HttpResponse
from django.forms.models import model_to_dict


import models
from models import (Item,
                    Bill,
                    Customer,
                    ProformaBill,
                    ProformaBillItem,
                    ClaveAcceso)
from company_accounts.models import (CompanyUser,
                                     Company,
                                     Establecimiento,
                                     PuntoEmision)
from company_accounts.licence_helpers import licence_required

from forms import (ItemForm,
                   ProformaBillForm,
                   ProformaBillAddItemForm,
                   ProformaBillItemForm,
                   CustomerForm)
from util import signature
from util import sri_sender
import accounts_receivable.models

tz = pytz.timezone('America/Guayaquil')


@login_required
def index(request):
    """
    Shows an index for the current user,
    showing the companies he can administer
    If there is a single company,
    it redirects to the company automatically
    """
    c_user = CompanyUser.objects.filter(user=request.user)
    if len(c_user) == 1:
        return redirect("company_index", c_user[0].company.id)
    param_dict = {
        'companies': Company.objects.filter(id__in=[cu.id for cu in c_user]),
        'user': request.user,
    }
    return render(request, "billing/index.html", param_dict)


class CompanySelected(object):
    """
    Class that offers the self.company attribute.
    The attribute checks that the company exists, or 404
    """
    @classmethod
    def as_view(cls, **initkwargs):
        view = super(CompanySelected, cls).as_view(**initkwargs)
        return login_required(view)

    @property
    def company(self):
        # Ensure there is a corresponding CompanyUser, or 404
        get_object_or_404(
            CompanyUser,
            user_id=self.request.user.id, company_id=self.company_id)
        return get_object_or_404(Company, id=self.company_id)

    @property
    def company_id(self):
        """
        Overridable property to get the current company id
        """
        return self.kwargs['company_id']

    def get_context_data(self, **kwargs):
        context = super(CompanySelected, self).get_context_data(**kwargs)
        context['company'] = self.company
        context['single_punto_emision'] = self.single_punto_emision
        return context

    @property
    def single_punto_emision(self):
        """
        Returns a PuntoEmision object if it's the only one
        for the current company
        """
        single_punto_emision = PuntoEmision.objects.filter(
            establecimiento__company=self.company)
        if len(single_punto_emision) == 1:
            return single_punto_emision[0]
        else:
            return None


class EstablecimientoSelected(CompanySelected):
    @property
    def establecimiento(self):
        return get_object_or_404(
            Establecimiento,
            id=self.establecimiento_id)

    @property
    def establecimiento_id(self):
        return self.kwargs['establecimiento_id']

    @property
    def company_id(self):
        return self.establecimiento.company.id

    def get_context_data(self, **kwargs):
        context = super(EstablecimientoSelected, self).get_context_data(**kwargs)
        context['establecimiento'] = self.establecimiento
        return context


class PuntoEmisionSelected(EstablecimientoSelected):
    @property
    def punto_emision(self):
        return get_object_or_404(
            PuntoEmision,
            id=self.punto_emision_id)

    @property
    def punto_emision_id(self):
        return self.kwargs["punto_emision_id"]

    @property
    def establecimiento_id(self):
        return self.punto_emision.establecimiento.id

    def get_context_data(self, **kwargs):
        context = super(PuntoEmisionSelected, self).get_context_data(**kwargs)
        context['punto_emision'] = self.punto_emision
        return context


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


class CompanyIndex(CompanySelected, View):
    """
    View that shows a general index for a given company
    """
    def get(self, request, company_id):
        """
        Shows an index for a company
        """
        company = self.company
        context = {}
        context.update({
            'item_list': (Item.objects
                          .filter(company=company)
                          .order_by('sku')[:5]),
            'bill_list': Bill.objects.filter(company=company),
            'proformabill_list':
                ProformaBill.objects
                .filter(punto_emision__establecimiento__company=company)
                .order_by("number")[:5],
            'customer_list':
                Customer.objects
                .filter(company=company).order_by('identificacion')[:5],
            'company': company,
            'single_punto_emision': self.single_punto_emision,
            'user': self.request.user,
        })
        return render(request, "billing/company_index.html", context)


####################################################################
#   Item views
####################################################################
class ItemView(object):
    """
    Base class for an Item View
    """
    model = Item
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
    template_name_suffix = '_create_form'
    form_class = ItemForm

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
    form_class = ItemForm

    def get_form(self, *args, **kwargs):
        form = super(ItemUpdateView, self).get_form(*args, **kwargs)
        item = Item.objects.get(pk=self.kwargs['pk'])
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


####################################################################
#   Customer views
####################################################################
class CustomerView(object):
    """
    Base class for an Item View
    """
    model = Customer
    context_object_name = 'customer'

    def get_queryset(self):
        return self.model.objects.filter(company=self.company)

    @property
    def company_id(self):
        return self.model.objects.get(id=self.kwargs['pk']).company.id


class CustomerListView(CompanySelected, CustomerView, ListView):
    context_object_name = "customer_list"


class CustomerDetailView(CustomerView, CompanySelected, DetailView):
    """
    Detail view for customers
    """


class CustomerCreateView(CompanySelected, CustomerView, CreateView):
    template_name_suffix = '_create_form'
    form_class = CustomerForm

    def form_valid(self, form):
        form.instance.company = self.company
        return super(self.__class__, self).form_valid(form)


class CustomerUpdateView(CustomerView, CompanySelected, UpdateView):
    form_class = CustomerForm


class CustomerDeleteView(CustomerView, CompanySelected, DeleteView):
    @property
    def success_url(self):
        view_name = "{}_index".format(self.context_object_name)
        return reverse(view_name, args=(self.company.id, ))


#############################################################
#   Proforma Bill views
#############################################################
class ProformaBillView(object):
    model = ProformaBill
    context_object_name = 'proformabill'

    def get_queryset(self):
        return (self.model.objects
                .filter(punto_emision__establecimiento__company=self.company))

    @property
    def punto_emision_id(self):
        return self.model.objects.get(id=self.kwargs['pk']).punto_emision.id


class ProformaBillCompanyListView(CompanySelected,
                                  ProformaBillView,
                                  ListView):
    context_object_name = "proformabill_list"


class ProformaBillEstablecimientoListView(EstablecimientoSelected,
                                          ProformaBillView,
                                          ListView):
    context_object_name = "proformabill_list"

    def get_queryset(self):
        return self.model.objects.filter(
            punto_emision__establecimiento=self.establecimiento)


class ProformaBillPuntoEmisionListView(PuntoEmisionSelected,
                                       ProformaBillView,
                                       ListView):
    context_object_name = "proformabill_list"

    def get_queryset(self):
        return self.model.objects.filter(punto_emision=self.punto_emision)


class ProformaBillDetailView(ProformaBillView,
                             PuntoEmisionSelected,
                             DetailView):
    """
    Detail view for proforma bills
    """
    def get_context_data(self, **kwargs):
        res = super(ProformaBillDetailView, self).get_context_data(**kwargs)
        fix_urls = {'45': ("asdf", 'Eliminar secuencial actual')}  # FIXME
        try:
            sri_errors = json.loads(self.proforma.issues)
        except:
            sri_errors = None

        if sri_errors:
            res['sri_errors'] = sri_errors
            for err in sri_errors:
                url = fix_urls.get(err['identificador'])
                if url:
                    err['url'] = url[0]
                    err['url_msg'] = url[1]
        return res


class ProformaBillDetailViewTable(ProformaBillView,
                             PuntoEmisionSelected,
                             DetailView):
    """
    Detail view for proforma bills
    """
    template_name_suffix = '_detail_item_table'


class ProformaBillPaymentView(ProformaBillView,
                              PuntoEmisionSelected,
                              DetailView):
    """
    Payment view for proforma bills
    """
    template_name_suffix = '_payment_form'

    def get_context_data(self, **kwargs):
        context = super(ProformaBillPaymentView, self).get_context_data(**kwargs)
        context['payment_kinds'] = models.FormaPago.objects.all()
        context['deferred'] = {}
        context['deferred']['payment_terms'] = models.PlazoPago.objects.exclude(tiempo=0)
        context['dues'] = {}
        context['dues']['payment_number_terms'] = range(2, 10)
        context['dues']['payment_terms'] = models.PlazoPago.objects.exclude(tiempo=0)
        return context

    def post(self, request, pk):
        proforma = self.get_queryset().get(pk=pk)
        # Delete previous payment terms
        payment_items = models.Pago.objects.filter(proforma_bill_id=proforma.id)
        for payment in payment_items:
            payment.delete()

        # Add new payment terms
        payment_method = models.FormaPago.objects.get(id=request.POST['payment_method'])
        if request.POST['payment_mode'] == 'immediate':
            installment = models.PlazoPago.objects.get(tiempo=0)
            models.Pago(porcentaje=Decimal(100),
                        forma_pago=payment_method,
                        plazo_pago=installment,
                        proforma_bill=proforma).save()
            return redirect("proformabill_detail", proforma.id)
        elif request.POST['payment_mode'] == 'deferred':
            installment = models.PlazoPago.objects.get(pk=request.POST['payment_time_to_pay'])
            models.Pago(porcentaje=Decimal(100),
                        forma_pago=payment_method,
                        plazo_pago=installment,
                        proforma_bill=proforma).save()
            return redirect("proformabill_detail", proforma.id)
        # elif request.POST['payment_mode'] == 'installments':
        #     return HttpResponse(str(("Cuotitas",
        #                         request.POST['payment_method'],
        #                         request.POST['payment_installments'],
        #                         request.POST['payment_time_between_installments'])))
        return HttpResponse("Ok")


class ProformaBillCreateView(PuntoEmisionSelected,
                             ProformaBillView,
                             View):
    template_name_suffix = '_create_form'
    form_class = ProformaBillForm

    def get(self, request, punto_emision_id):
        company = self.company
        proforma_no = company.siguiente_numero_proforma
        company.siguiente_numero_proforma = proforma_no + 1
        company.save()
        new_proforma = models.ProformaBill(
            number='P-{:08d}'.format(proforma_no),
            date=datetime.now(tz=pytz.timezone('America/Guayaquil')),
            punto_emision=self.punto_emision,
            issued_to=None)
        new_proforma.save()
        return redirect('proformabill_detail', new_proforma.id)


class ProformaBillUpdateView(ProformaBillView,
                             PuntoEmisionSelected,
                             UpdateView):
    form_class = ProformaBillForm

    def get_form(self, *args, **kwargs):
        form = super(self.__class__, self).get_form(*args, **kwargs)
        c, created = models.Customer.objects.get_or_create(
            razon_social='CONSUMIDOR FINAL',
            tipo_identificacion='ruc',
            identificacion='9999999999999',
            company=self.company)
        if form.data.get("cons_final") == 'True':
            print "TRRT"
            form.data = form.data.copy()
            form.data['issued_to'] = c.id
            form.fields['issued_to'].queryset = Customer.objects.filter(
                company=self.company)
        else:
            form.fields['issued_to'].queryset = Customer.objects.filter(
                company=self.company).exclude(identificacion='9999999999999')
        return form


class ProformaBillDeleteView(ProformaBillView,
                             PuntoEmisionSelected,
                             DeleteView):
    @property
    def success_url(self):
        view_name = "{}_company_index".format(self.context_object_name)
        return reverse(view_name, args=(self.company.id, ))


#############################################################
#   Proforma Bill Emit Bill views
#############################################################
@licence_required('basic', 'professional', 'enterprise')
class ProformaBillEmitView(ProformaBillView, PuntoEmisionSelected, DetailView):
    template_name_suffix = '_emit'

    def get_context_data(self, **kwargs):
        res = super(ProformaBillEmitView, self).get_context_data(**kwargs)
        try:
            res['msgs'] = self.error_messages
        except:
            pass
        return res

    def post(self, request, pk):
        # Local vars
        proforma = self.get_object()
        punto_emision = proforma.punto_emision
        establecimiento = punto_emision.establecimiento
        company = establecimiento.company

        ambiente = punto_emision.ambiente_sri
        secuencial = {
            'pruebas': punto_emision.siguiente_secuencial_pruebas,
            'produccion': punto_emision.siguiente_secuencial_produccion,
        }[ambiente]

        numero_comprobante = "{}-{}-{:09d}".format(establecimiento.codigo,
                                                   punto_emision.codigo,
                                                   secuencial)

        # Generate and sign XML
        xml_data, clave_acceso = gen_bill_xml(request, proforma)
        assert(clave_acceso == proforma.clave_acceso)
        print "Claves de acceso coinciden"

        proforma.xml_content = xml_data
        proforma.clave_acceso = clave_acceso
        proforma.save()

        # Send XML to SRI 
        enviar_comprobante_result = sri_sender.enviar_comprobante(xml_data)
        enviar_msgs = enviar_comprobante_result.comprobantes.comprobante[0].mensajes.mensaje

        def convert_messages(messages):
            def convert_msg(msg):
                converted = {}
                for key in ['tipo', 'identificador', 'mensaje', 'informacionAdicional']:
                    converted[key] = getattr(error, key, None)
            return map(convert_msg, messages)

        # True if any of the error messages is 43: repeated access key
        used_access_key_error = any(map(lambda x: x.identificador == '43', enviar_msgs))

        if enviar_comprobante_result.estado == 'DEVUELTA' and not used_access_key_error:
            proforma.issues = json.dumps(convert_messages(enviar_msgs))
            proforma.save()
            return redirect("proformabill_detail", proforma.id)

        # Check result
        def validar_comprobante(clave):
            for i in range(10):
                print "Validando", i
                validar_result = sri_sender.validar_comprobante(clave)
                try:
                    if validar_result.autorizaciones[0][0].estado in ['AUTORIZADO', 'NO AUTORIZADO']:
                        return validar_result.autorizaciones[0][0]
                except Exception, e:
                    print e
                    pass
                time.sleep(1)
            return None
        autorizacion = validar_comprobante(clave_acceso)

        if not autorizacion:
            proforma.issues = json.dumps([{'tipo': 'ERROR',
                                              'identificador': '',
                                              'mensaje': 'Tiempo de espera agotado'}])
            proforma.save()
            return redirect("proformabill_detail", proforma.id)

        if autorizacion.estado != 'AUTORIZADO':
            proforma.issues = json.dumps(convert_messages(autorizacion.mensajes))
            proforma.save()
            return redirect("proformabill_detail", proforma.id)

        # Accepted
        # convert to bill
        new = models.Bill.fromProformaBill(proforma)
        new.numero_autorizacion = autorizacion.numeroAutorizacion
        new.fecha_autorizacion = autorizacion.fechaAutorizacion
        new.xml_content = autorizacion.comprobante
        new.clave_acceso = clave_acceso
        new.iva = sum(proforma.iva.values())
        new.iva_retenido = 0
        new.total_sin_iva = sum(proforma.subtotal.values())
        new.ambiente_sri = autorizacion.ambiente.lower()
        new.number = numero_comprobante
        new.issues = json.dumps(convert_messages(autorizacion.mensajes))
        new.save()

        # Generate Receivables
        for payment in proforma.payment:
            if payment.plazo_pago.unidad_tiempo == 'dias':
                payment_date = date.today() + timedelta(days=payment.plazo_pago.tiempo)
            r = accounts_receivable.models.Receivable(
                    bill=new,
                    qty=payment.cantidad,
                    date=payment_date,
                    method=payment.forma_pago)
            r.save()

        # update sequence numbers
        if ambiente == 'pruebas':
            punto_emision.siguiente_secuencial_pruebas = secuencial + 1
        else:
            punto_emision.siguiente_secuencial_produccion = secuencial + 1
        punto_emision.save()

        # generate RIDE
        # FIXME
        
        # Remove proforma
        for item in proforma.items:
            item.delete()
        proforma.delete()
        # redirect to bill
        return redirect("bill_detail", new.id)


def gen_bill_xml(request, proformabill):

    def get_code_from_proforma_number(number):
        for i in range(len(number)):
            try:
                assert(int(number[i:]) >= 0)
                return int(number[i:])
            except (ValueError, AssertionError):
                pass
        else:
            return 0

    company = proformabill.punto_emision.establecimiento.company

    context = {
        'proformabill': proformabill,
        'punto_emision': proformabill.punto_emision,
        'establecimiento': proformabill.punto_emision.establecimiento,
        'company': company,
    }

    ambiente_sri = proformabill.punto_emision.ambiente_sri
    secuencial = {
        'pruebas': proformabill.punto_emision.siguiente_secuencial_pruebas,
        'produccion': proformabill.punto_emision.siguiente_secuencial_produccion
    }[ambiente_sri]

    context['secuencial'] = secuencial

    info_tributaria = {}
    info_tributaria['ambiente'] = {
        'pruebas': '1',
        'produccion': '2'
    }[ambiente_sri]

    info_tributaria['tipo_emision'] = '1'   # 1: normal
                                            # 2: indisponibilidad sistema
    info_tributaria['cod_doc'] = '01'   # 01: factura
                                        # 04: nota de credito
                                        # 05: nota de debito
                                        # 06: guia de remision
                                        # 07: comprobante de retencion
    c = ClaveAcceso()
    proformabill.date = proformabill.date.astimezone(
        pytz.timezone('America/Guayaquil'))
    c.fecha_emision = (proformabill.date.year,
                       proformabill.date.month,
                       proformabill.date.day)
    c.tipo_comprobante = "factura"
    c.ruc = str(company.ruc)
    c.ambiente = proformabill.punto_emision.ambiente_sri
    c.establecimiento = int(proformabill.punto_emision.establecimiento.codigo)
    c.punto_emision = int(proformabill.punto_emision.codigo)
    c.numero = secuencial
    c.codigo = get_code_from_proforma_number(proformabill.number)
    c.tipo_emision = "normal"
    clave_acceso = unicode(c)
    info_tributaria['clave_acceso'] = clave_acceso

    context['info_tributaria'] = info_tributaria

    info_factura = {}
    info_factura['tipo_identificacion_comprador'] = {    # tabla 7
        'ruc': '04',
        'cedula': '05',
        'pasaporte': '06',
        'consumidor_final': '07',
        'exterior': '08',
        'placa': '09',
    }[proformabill.issued_to.tipo_identificacion]
    info_factura['total_descuento'] = 0     # No hay descuentos
    info_factura['propina'] = 0             # No hay propinas
    info_factura['moneda'] = 'DOLAR'
    context['info_factura'] = info_factura

    context['info_adicional'] = {
        'Generado Con': 'DSSTI Facturas',
        'Web': 'http://facturas.dssti.com',
    }

    response = render(request, "billing/proformabill_xml.html", context)

    xml_content = response.content
    # sign xml_content
    return signature.sign(company.ruc, company.id, xml_content), clave_acceso


@licence_required('basic', 'professional', 'enterprise')
class ProformaBillEmitGenXMLView(ProformaBillView,
                                 PuntoEmisionSelected,
                                 View):

    def get(self, request, pk):
        proformabill = self.get_queryset().get(id=pk)
        xml = gen_bill_xml(request, proformabill)
        return HttpResponse(xml)


#############################################################
#   Proforma Bill Item views
#############################################################
class ProformaBillSelected(PuntoEmisionSelected):
    model = ProformaBillItem
    context_object_name = 'item'

    @property
    def proformabill(self):
        """
        Attribute that returns the current proformabill
        """
        return get_object_or_404(ProformaBill,
                                 id=self.proformabill_id)

    @property
    def proformabill_id(self):
        return self.kwargs['proformabill_id']

    @property
    def punto_emision_id(self):
        return self.proformabill.punto_emision.id

    def get_context_data(self, **kwargs):
        """
        Adds proformabill to the context data
        """
        context = super(ProformaBillSelected, self).get_context_data(**kwargs)
        context['proformabill'] = self.proformabill
        return context

    @property
    def success_url(self):
        """
        Generic success URL, goes back to the proforma bill detail view
        """
        return reverse("proformabill_detail",
                       args=(self.proformabill.id,))


class ProformaBillItemView(object):
    model = ProformaBillItem
    context_object_name = 'item'

    def get_queryset(self):
        return self.model.objects.filter(proforma_bill=self.proformabill)

    @property
    def proformabill_id(self):
        return self.model.objects.get(id=self.kwargs['pk']).proforma_bill.id


class ProformaBillAddItemView(ProformaBillSelected,
                              CreateView):
    template_name_suffix = '_create_form'
    form_class = ProformaBillAddItemForm

    def get_form(self, *args, **kwargs):
        form = super(self.__class__, self).get_form(*args, **kwargs)
        form.fields['copy_from'].queryset = Item.objects.filter(
            company=self.company)
        return form

    def form_valid(self, form):
        copy_from = form.cleaned_data["copy_from"]
        copy_from = (Item.objects
                     .filter(company=self.company)
                     .get(id=copy_from.id))
        form.instance.proforma_bill = self.proformabill

        item_vals = {}
        for field in copy_from.__dict__.keys():
            if field.startswith("_"):
                continue
            if field.endswith("_id"):
                continue
            if field in ['qty', 'id']:
                continue
            item_vals[field] = getattr(copy_from, field)

        current_item = ProformaBillItem.objects.filter(**item_vals)
        for k, v in item_vals.iteritems():
            setattr(form.instance, k, v)
        if current_item:
            form.instance.id = current_item[0].id
            form.instance.qty = current_item[0].qty + form.instance.qty
        res = super(self.__class__, self).form_valid(form)
        form.instance.tax_items.add(copy_from.iva)
        if copy_from.ice:
            form.instance.tax_items.add(copy_from.ice)
        return res


class ProformaBillItemUpdateView(ProformaBillItemView,
                                 ProformaBillSelected,
                                 UpdateView):
    template_name_suffix = '_form'
    form_class = ProformaBillItemForm

    def form_valid(self, form):
        form.instance.proforma_bill = self.proformabill
        res = super(self.__class__, self).form_valid(form)
        return res


class ProformaBillItemUpdateViewJS(ProformaBillItemView,
                                   ProformaBillSelected,
                                   View):
    def post(self, request, pk):
        proformabill_item = get_object_or_404(
            self.model, proforma_bill=self.proformabill, pk=pk)

        def accept_qty(val):
            val = Decimal(val)
            if val < 0:
                raise Exception("Invalid QTY")
            return val
        for field, fun in [('qty', accept_qty)]:
            val = request.POST[field]
            setattr(proformabill_item, field, fun(val))
        proformabill_item.full_clean()
        if proformabill_item.qty == 0:
            proformabill_item.delete()
        else:
            proformabill_item.save()
        return HttpResponse("Ok")


class ProformaBillItemDeleteView(ProformaBillItemView,
                                 ProformaBillSelected,
                                 DeleteView):
    """
    Delete view for proformabill items
    """


################
# Bill Reports #
################
class BillView(object):
    model = Bill
    context_object_name = 'bill'

    def get_queryset(self):
        return self.model.objects.filter(company=self.company)

    @property
    def company_id(self):
        return self.model.objects.get(id=self.kwargs['pk']).company.id


class BillDayListReport(BillView, CompanySelected, ListView):
    context_object_name = "bill_list"

    def get_queryset(self):
        start_date = datetime(int(self.kwargs['year']),
                              int(self.kwargs['month']),
                              int(self.kwargs['day']))
        end_date = start_date + timedelta(days=1)
        return (self.model.objects
                .filter(company=self.company)
                .filter(date__gte=start_date, date__lt=end_date))

    def get_context_data(self, **kwargs):
        context = super(BillDayListReport, self).get_context_data(**kwargs)
        for key in ['year', 'month', 'day']:
            context[key] = self.kwargs[key]
        return context

class BillListView(BillView, CompanySelected, ListView):
    context_object_name = "bill_list"

    @property
    def company_id(self):
        return self.kwargs['company_id']


class BillDetailView(BillView, CompanySelected, DetailView):
    """
    """
