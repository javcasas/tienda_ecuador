# * encoding: utf-8 *
import pytz
import time
import json
from datetime import datetime, timedelta, date
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


from billing import models
from billing import forms
from company_accounts.models import (CompanyUser,
                                     Company,
                                     Establecimiento,
                                     PuntoEmision)
from company_accounts.licence_helpers import licence_required
import inventory.models

from util import signature
from util import sri_sender
from sri.models import SRIStatus
from util import mail
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
            'item_list': [],
            #    models.Item.objects
            #               .filter(company=company)
            #               .order_by('sku')[:5],
            'bill_list':
                models.Bill.objects
                           .filter(company=company)
                           .filter(status=SRIStatus.options.Accepted)[:5],
            'prebill_list':
                models.Bill.objects
                           .filter(punto_emision__establecimiento__company=company)
                           .filter(status=SRIStatus.options.NotSent)
                           .order_by("number")[:5],
            'customer_list':
                models.Customer.objects
                               .filter(company=company)
                               .exclude(identificacion='9999999999999')
                               .order_by('identificacion')[:5],
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
    #model = models.Item
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
    #form_class = forms.ItemForm

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
    #form_class = forms.ItemForm

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


####################################################################
#   Customer views
####################################################################
class CustomerView(object):
    """
    Base class for an Item View
    """
    model = models.Customer
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
    form_class = forms.CustomerForm

    def form_valid(self, form):
        form.instance.company = self.company
        return super(self.__class__, self).form_valid(form)


class CustomerUpdateView(CustomerView, CompanySelected, UpdateView):
    form_class = forms.CustomerForm


class CustomerDeleteView(CustomerView, CompanySelected, DeleteView):
    def get_success_url(self):
        view_name = "{}_index".format(self.context_object_name)
        return reverse(view_name, args=(self.company.id, ))


#############################################################
#   Proforma Bill views
#############################################################
class BillView(object):
    model = models.Bill
    context_object_name = 'bill'
    queryset_filters = {}

    def get_queryset(self):
        return (self.model.objects
                .filter(punto_emision__establecimiento__company=self.company)
                .filter(**self.queryset_filters))

    @property
    def punto_emision_id(self):
        return self.model.objects.get(id=self.kwargs['pk']).punto_emision.id

    @property
    def company_id(self):
        return self.model.objects.get(id=self.kwargs['pk']).company.id


class BillSelected(PuntoEmisionSelected):
    model = models.BillItem
    context_object_name = 'item'

    @property
    def bill(self):
        """
        Attribute that returns the current bill
        """
        return get_object_or_404(models.Bill,
                                 id=self.bill_id)

    @property
    def bill_id(self):
        return self.kwargs['bill_id']

    @property
    def punto_emision_id(self):
        return self.bill.punto_emision.id

    def get_context_data(self, **kwargs):
        """
        Adds bill to the context data
        """
        context = super(BillSelected, self).get_context_data(**kwargs)
        context['bill'] = self.bill
        return context

    def get_success_url(self):
        """
        Generic success URL, goes back to the proforma bill detail view
        """
        return reverse("bill_detail",
                       args=(self.bill.id,))


class BillItemView(object):
    model = models.BillItem
    context_object_name = 'item'

    def get_queryset(self):
        return self.model.objects.filter(bill=self.bill)

    @property
    def bill_id(self):
        return self.model.objects.get(id=self.kwargs['pk']).bill.id


class BillCompanyListView(CompanySelected,
                          BillView,
                          ListView):
    context_object_name = "bill_list"


class BillEstablecimientoListView(EstablecimientoSelected,
                                  BillView,
                                  ListView):
    context_object_name = "bill_list"

    def get_queryset(self):
        return self.model.objects.filter(
            punto_emision__establecimiento=self.establecimiento)


class BillPuntoEmisionListView(PuntoEmisionSelected,
                               BillView,
                               ListView):
    context_object_name = "bill_list"

    def get_queryset(self):
        return self.model.objects.filter(punto_emision=self.punto_emision)


class BillDetailView(BillView,
                     PuntoEmisionSelected,
                     DetailView):
    """
    Detail view for proforma bills
    """
    def get_context_data(self, **kwargs):
        res = super(BillDetailView, self).get_context_data(**kwargs)
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


class BillDetailViewTable(BillView,
                          PuntoEmisionSelected,
                          DetailView):
    """
    Detail view for proforma bills
    """
    template_name_suffix = '_detail_item_table'


class BillPaymentView(BillView,
                      PuntoEmisionSelected,
                      DetailView):
    """
    Payment view for proforma bills
    """
    template_name_suffix = '_payment_form'

    def get_context_data(self, **kwargs):
        context = super(BillPaymentView, self).get_context_data(**kwargs)
        context['payment_kinds'] = models.FormaPago.objects.all()
        context['deferred'] = {}
        context['deferred']['payment_terms'] = models.PlazoPago.objects.exclude(tiempo=0)
        context['dues'] = {}
        context['dues']['payment_number_terms'] = range(2, 10)
        context['dues']['payment_terms'] = models.PlazoPago.objects.exclude(tiempo=0)
        return context

    def post(self, request, pk):
        bill = self.model.objects.get(id=pk)
        # Delete previous payment terms
        payment_items = models.Pago.objects.filter(bill=bill)
        for payment in payment_items:
            payment.delete()

        # Add new payment terms
        payment_method = models.FormaPago.objects.get(
            id=request.POST['payment_method'])

        if request.POST['payment_mode'] == 'immediate':
            installment = models.PlazoPago.objects.get(tiempo=0)
            models.Pago(porcentaje=Decimal(100),
                        forma_pago=payment_method,
                        plazo_pago=installment,
                        bill=bill).save()
            return redirect("bill_detail", bill.id)
        elif request.POST['payment_mode'] == 'deferred':
            installment = models.PlazoPago.objects.get(
                pk=request.POST['payment_time_to_pay'])
            models.Pago(porcentaje=Decimal(100),
                        forma_pago=payment_method,
                        plazo_pago=installment,
                        bill=bill).save()
            return redirect("bill_detail", bill.id)
        # elif request.POST['payment_mode'] == 'installments':
        #     return HttpResponse(str(("Cuotitas",
        #                         request.POST['payment_method'],
        #                         request.POST['payment_installments'],
        #                         request.POST['payment_time_between_installments'])))
        return HttpResponse("Ok")


class BillCreateView(PuntoEmisionSelected,
                     BillView,
                     View):
    template_name_suffix = '_create_form'
    form_class = forms.BillForm

    def get(self, request, punto_emision_id):
        company = self.company
        proforma_no = company.siguiente_numero_proforma
        company.siguiente_numero_proforma = proforma_no + 1
        company.save()
        new_bill = models.Bill(
            number='P-{:08d}'.format(proforma_no),
            date=datetime.now(tz=pytz.timezone('America/Guayaquil')),
            punto_emision=self.punto_emision,
            company=self.company,
            issued_to=None)
        new_bill.save()
        return redirect('bill_detail', new_bill.id)


class BillUpdateView(BillView,
                     PuntoEmisionSelected,
                     UpdateView):
    form_class = forms.BillForm

    def get_form(self, *args, **kwargs):
        form = super(self.__class__, self).get_form(*args, **kwargs)
        c, created = models.Customer.objects.get_or_create(
            razon_social='CONSUMIDOR FINAL',
            tipo_identificacion='ruc',
            identificacion='9999999999999',
            company=self.company)
        if form.data.get("cons_final") == 'True':
            form.data = form.data.copy()
            form.data['issued_to'] = c.id
            form.fields['issued_to'].queryset = models.Customer.objects.filter(
                company=self.company)
        else:
            form.fields['issued_to'].queryset = models.Customer.objects.filter(
                company=self.company).exclude(identificacion='9999999999999')
        return form


class BillNewCustomerView(BillSelected,
                          PuntoEmisionSelected,
                          CreateView):
    form_class = forms.CustomerForm
    model = models.Customer
    template_name = 'billing/bill_new_customer_form.html'

    def form_valid(self, form):
        form.instance.company = self.company
        res = super(BillNewCustomerView, self).form_valid(form)
        bill = self.bill
        bill.issued_to = form.instance
        bill.save()
        return res

    def get_success_url(self):
        return reverse('bill_detail', args=(self.bill.id, ))


class BillDeleteView(BillView,
                     PuntoEmisionSelected,
                     DeleteView):

    def get_success_url(self):
        view_name = "{}_company_index".format(self.context_object_name)
        return reverse(view_name, args=(self.company.id, ))


class BillSendToCustomerView(BillView,
                             PuntoEmisionSelected,
                             DetailView):
    """
    Send proformas to customers
    """
    def get_context_data(self, **kwargs):
        context = super(BillSendToCustomerView, self).get_context_data(**kwargs)
        context['form'] = forms.SendToCustomerForm(
            initial={'subject': 'Proforma de {}'.format(self.company.nombre_comercial or
                                                        self.company.razon_social),
                     'text': u"Estimado Sr,\nAdjunto la proforma que me pidió.\nSaludos cordiales"}
        )
        return context

    def post(self, request, pk):
        bill = self.get_object()
        self.object = bill
        filename = "Proforma_{}.pdf".format(bill.number)
        filecontent = bill.gen_pdf()
        subject = request.POST['subject']
        text = request.POST['text']
        mail.send_mail(request.user.email,
                       bill.issued_to.email,
                       subject,
                       text,
                       [("application/pdf", filename, filecontent)])
        return render(request, "billing/bill_send_to_customer_sent.html", self.get_context_data())


#############################################################
#   Proforma Bill Emit Bill views
#############################################################
@licence_required('basic', 'professional', 'enterprise')
class BillEmitAutoProgressView(BillView, PuntoEmisionSelected, DetailView):
    """
    Confirms acceptance of bill, moves it to the 'a enviar' status
    """
    template_name_suffix = '_emit'

    def get_context_data(self, **kwargs):
        res = super(BillEmitAutoProgressView, self).get_context_data(**kwargs)
        try:
            res['msgs'] = self.error_messages
        except:
            pass
        return res

    def post(self, request, pk):
        self.object = self.get_object()
        return render(request, "billing/bill_emit_auto_progress.html", self.get_context_data())


@licence_required('basic', 'professional', 'enterprise')
class BillEmitAcceptView(BillView, PuntoEmisionSelected, DetailView):
    """
    Confirms acceptance of bill, moves it to the 'a enviar' status
    """
    template_name_suffix = '_emit'

    def get_context_data(self, **kwargs):
        res = super(BillEmitAcceptView, self).get_context_data(**kwargs)
        try:
            res['msgs'] = self.error_messages
        except:
            pass
        return res

    def post(self, request, pk):
        # Local vars
        def success(msg):
            return HttpResponse(
                json.dumps({
                    'success': True,
                    'msg': msg
                }))

        bill = self.get_object()
        if bill.status in [SRIStatus.options.ReadyToSend, SRIStatus.options.Sent,
                           SRIStatus.options.Accepted, SRIStatus.options.Annulled]:
            return success('Ya Aceptado')
        if bill.status != SRIStatus.options.NotSent:
            return HttpResponse("Bill status is not 'NotSent'",
                                status=412, reason='Precondition Failed')
        if not bill.punto_emision:
            return HttpResponse("Bill has no 'punto_emision'",
                                status=412, reason='Precondition Failed')
        bill.date = datetime.now(tz=pytz.timezone('America/Guayaquil'))
        bill.save()
        bill.accept()
        return success('Aceptado')


@licence_required('basic', 'professional', 'enterprise')
class BillEmitSendToSRIView(BillView, PuntoEmisionSelected, DetailView):
    """
    Sends an 'a enviar' bill to SRI
    """
    template_name_suffix = '_disabled'

    def post(self, request, pk):
        def success(msg):
            return HttpResponse(
                json.dumps({
                    'success': True,
                    'msg': msg
                }))
        def failure(msg):
            return HttpResponse(
                json.dumps({
                    'success': False,
                    'msg': msg
                }))

        bill = self.get_object()
        if bill.status in [SRIStatus.options.Sent,
                           SRIStatus.options.Accepted,
                           SRIStatus.options.Annulled]:
            return success("Ya enviado")
        if bill.status != SRIStatus.options.ReadyToSend:
            return HttpResponse("Bill status is not 'a enviar'",
                                status=412, reason='Precondition Failed')

        send_res = bill.send_to_SRI()
        if send_res:
            return success("Enviado")
        else:
            return failure("Factura rechazada")


@licence_required('basic', 'professional', 'enterprise')
class BillEmitValidateView(BillView, PuntoEmisionSelected, DetailView):
    """
    Sends an 'a enviar' bill to SRI
    """
    template_name_suffix = '_disabled'

    def post(self, request, pk):
        def success(msg):
            return HttpResponse(
                json.dumps({
                    'success': True,
                    'msg': msg
                }))
        def failure(msg):
            return HttpResponse(
                json.dumps({
                    'success': False,
                    'msg': msg
                }))
        def not_yet(msg):
            return HttpResponse(
                json.dumps({
                    'success': False,
                    'msg': msg
                }))
        bill = self.get_object()
        if bill.status in [SRIStatus.options.Accepted, SRIStatus.options.Annulled]:
            return success("Ya Validado")
        if bill.status in [SRIStatus.options.NotSent]:
            return failure("Ya Rechazado")
        if bill.status != SRIStatus.options.Sent:
            return HttpResponse("Bill status is not 'sent'",
                                status=412, reason='Precondition Failed')

        res = bill.validate_in_SRI()
        if res:
            return success("Aceptado")
        elif bill.status == SRIStatus.options.NotSent:
            return failure("Rechazado")
        elif bill.status == SRIStatus.options.Sent:
            return HttpResponse(u"Aún no procesada", status=412, reason='Precondition Failed')


@licence_required('basic', 'professional', 'enterprise')
class BillEmitCheckAnnulledView(BillView, PuntoEmisionSelected, DetailView):
    """
    Checks if the bill has been annulled
    """
    template_name_suffix = '_disabled'

    def post(self, request, pk):
        bill = self.get_object()
        if bill.status != SRIStatus.options.Accepted:
            return HttpResponse("Bill status is not 'Accepted'",
                                status=412, reason='Precondition Failed')

        res = bill.check_if_annulled_in_SRI()
        if res:
            return HttpResponse("Anulled")
        else:
            return HttpResponse("Not annulled")


class BillEmitGeneralProgressView(View):
    """
    Progresses bill statuses
    """
    def get(self, request):
        max_bills_to_process = 3
        left_slots = self.send_bills_to_SRI(max_bills_to_process)
        left_slots = self.validate_bills_in_SRI(left_slots)
        left_slots = self.check_if_annulled_in_SRI(left_slots)
        return HttpResponse("Ok, {} slots left".format(left_slots))

    def send_bills_to_SRI(self, num_bills):
        if num_bills == 0:
            return 0
        bills_to_send = models.Bill.objects.filter(status=SRIStatus.options.ReadyToSend)[:num_bills]
        for bill in bills_to_send:
            bill.send_to_SRI()
        return num_bills - len(bills_to_send)

    def validate_bills_in_SRI(self, num_bills):
        if num_bills == 0:
            return 0
        bills_to_validate = models.Bill.objects.filter(status=SRIStatus.options.Sent)[:num_bills]
        for bill in bills_to_validate:
            bill.validate_in_SRI()
        return num_bills - len(bills_to_validate)

    def check_if_annulled_in_SRI(self, num_bills):
        if num_bills == 0:
            return 0
        now = datetime.now(tz=pytz.timezone('America/Guayaquil'))
        accepted_bills = (models.Bill.objects
                          .filter(status=SRIStatus.options.Accepted)
                          .filter(fecha_autorizacion__gte=now-timedelta(days=15)))
        unchecked_bills = accepted_bills.filter(sri_last_check=None)
        not_too_checked = accepted_bills.filter(sri_last_check__lte=now-timedelta(hours=1))
        to_check = (unchecked_bills | not_too_checked).order_by("?")[:num_bills]
        for bill in to_check:
            bill.check_if_annulled_in_SRI()
        return num_bills - len(to_check)


@licence_required('basic', 'professional', 'enterprise')
class BillEmitView(BillView, PuntoEmisionSelected, DetailView):
    template_name_suffix = '_emit'

    def get_context_data(self, **kwargs):
        res = super(BillEmitView, self).get_context_data(**kwargs)
        try:
            res['msgs'] = self.error_messages
        except:
            pass
        return res

    def post(self, request, pk):
        # Local vars
        bill = self.get_object()
        punto_emision = bill.punto_emision
        establecimiento = punto_emision.establecimiento

        ambiente = punto_emision.ambiente_sri
        secuencial = {
            'pruebas': punto_emision.siguiente_secuencial_pruebas,
            'produccion': punto_emision.siguiente_secuencial_produccion,
        }[ambiente]

        numero_comprobante = "{}-{}-{:09d}".format(establecimiento.codigo,
                                                   punto_emision.codigo,
                                                   secuencial)

        # Generate and sign XML
        xml_data, clave_acceso = gen_bill_xml(request, bill)
        # assert(clave_acceso == proforma.clave_acceso) FIXME: Is this needed?
        # print "Claves de acceso coinciden"

        bill.xml_content = xml_data
        bill.clave_acceso = clave_acceso
        bill.save()

        # Send XML to SRI
        enviar_comprobante_result = sri_sender.enviar_comprobante(xml_data)
        enviar_msgs = (enviar_comprobante_result.comprobantes.comprobante[0]
                                                .mensajes.mensaje)

        def convert_messages(messages):
            def convert_msg(msg):
                converted = {}
                for key in ['tipo', 'identificador',
                            'mensaje', 'informacionAdicional']:
                    converted[key] = getattr(msg, key, None)
            return map(convert_msg, messages)

        # True if any of the error messages is 43: repeated access key
        used_access_key_error = any(
            map(lambda x: x.identificador == '43', enviar_msgs))

        if (enviar_comprobante_result.estado == 'DEVUELTA'
                and not used_access_key_error):
            bill.issues = json.dumps(convert_messages(enviar_msgs))
            bill.save()
            return redirect("bill_detail", bill.id)

        # Check result
        def validar_comprobante(clave):
            for i in range(10):
                print "Validando", i
                validar_result = sri_sender.validar_comprobante(clave)
                try:
                    if (validar_result.autorizaciones[0][0].estado
                            in ['AUTORIZADO', 'NO AUTORIZADO']):
                        return validar_result.autorizaciones[0][0]
                except Exception, e:
                    print e
                    pass
                time.sleep(1)
            return None
        autorizacion = validar_comprobante(clave_acceso)

        if not autorizacion:
            bill.issues = json.dumps([{'tipo': 'ERROR',
                                       'identificador': '',
                                       'mensaje': 'Tiempo de espera agotado'}])
            bill.save()
            return redirect("bill_detail", bill.id)

        if autorizacion.estado != 'AUTORIZADO':
            bill.issues = json.dumps(convert_messages(autorizacion.mensajes))
            bill.save()
            return redirect("bill_detail", bill.id)

        # Accepted
        # convert to bill
        new = models.Bill.fromProformaBill(bill)
        new.numero_autorizacion = autorizacion.numeroAutorizacion
        new.fecha_autorizacion = autorizacion.fechaAutorizacion
        new.xml_content = autorizacion.comprobante
        new.clave_acceso = clave_acceso
        new.iva = sum(bill.iva.values())
        new.iva_retenido = 0
        new.total_sin_iva = sum(bill.subtotal.values())
        new.ambiente_sri = autorizacion.ambiente.lower()
        new.number = numero_comprobante
        new.issues = json.dumps(convert_messages(autorizacion.mensajes))
        new.save()

        # Generate Receivables
        for payment in bill.payment:
            if payment.plazo_pago.unidad_tiempo == 'dias':
                payment_date = (date.today()
                                + timedelta(days=payment.plazo_pago.tiempo))
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
        for item in bill.items:
            item.delete()
        bill.delete()
        # redirect to bill
        return redirect("bill_detail", new.id)


def gen_bill_xml(request, bill, codigo=None):
    """
    Generates XML content and clave de acceso
    Requires bill with:
        punto_emision
        ambiente_sri
        secuencial
        date
    @returns: signed_xml_content, clave_acceso
    """
    def get_code_from_proforma_number(number):
        for i in range(len(number)):
            try:
                assert(int(number[i:]) >= 0)
                assert(int(number[i:]) < 10 ** 8)
                return int(number[i:])
            except (ValueError, AssertionError):
                pass
        else:
            return 0

    assert bill.punto_emision
    assert bill.ambiente_sri
    assert bill.secuencial
    assert bill.date

    company = bill.punto_emision.establecimiento.company

    context = {
        'proformabill': bill,
        'punto_emision': bill.punto_emision,
        'establecimiento': bill.punto_emision.establecimiento,
        'company': company,
    }

    context['secuencial'] = bill.secuencial

    info_tributaria = {}
    info_tributaria['ambiente'] = {
        'pruebas': '1',
        'produccion': '2'
    }[bill.ambiente_sri]

    info_tributaria['tipo_emision'] = '1'   # 1: normal
                                            # 2: indisponibilidad sistema
    info_tributaria['cod_doc'] = '01'   # 01: factura
                                        # 04: nota de credito
                                        # 05: nota de debito
                                        # 06: guia de remision
                                        # 07: comprobante de retencion
    c = models.ClaveAcceso()
    # proformabill.date = proformabill.date.astimezone(
    #     pytz.timezone('America/Guayaquil'))  # FIXME
    c.fecha_emision = (bill.date.year,
                       bill.date.month,
                       bill.date.day)
    c.tipo_comprobante = "factura"
    c.ruc = str(company.ruc)
    c.ambiente = bill.ambiente_sri
    c.establecimiento = int(bill.punto_emision.establecimiento.codigo)
    c.punto_emision = int(bill.punto_emision.codigo)
    c.numero = bill.secuencial
    c.codigo = codigo or get_code_from_proforma_number(bill.number)
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
    }[bill.issued_to.tipo_identificacion]
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
    signed_xml_content = signature.sign(company.ruc, company.id, xml_content)
    return signed_xml_content, clave_acceso


@licence_required('basic', 'professional', 'enterprise')
class BillEmitGenXMLView(BillView,
                         PuntoEmisionSelected,
                         View):

    def get(self, request, pk):
        proformabill = self.get_queryset().get(id=pk)
        xml = gen_bill_xml(request, proformabill)
        return HttpResponse(xml)


#############################################################
#   Proforma Bill Item views
#############################################################


class BillAddItemView(BillSelected,
                      CreateView):
    template_name_suffix = '_create_form'
    form_class = forms.BillAddItemForm

    def get_form(self, *args, **kwargs):
        form = super(self.__class__, self).get_form(*args, **kwargs)
        form.fields['sku'].queryset = inventory.models.SKU.objects.filter(
            batch__item__company=self.company)
        return form

    def form_valid(self, form):
        form.instance.bill = self.bill
        # Add item to existing one if exists
        try:
            prev = self.model.objects.get(bill=self.bill, sku=form.instance.sku)
            form.instance.id = prev.id
            form.instance.qty += 1
        except self.model.DoesNotExist:
            pass
        return super(BillAddItemView, self).form_valid(form)


class BillItemUpdateView(BillItemView,
                         BillSelected,
                         UpdateView):
    template_name_suffix = '_form'
    form_class = forms.BillItemForm

    def form_valid(self, form):
        form.instance.bill = self.bill
        res = super(BillItemUpdateView, self).form_valid(form)
        return res


class BillItemUpdateViewJS(BillItemView,
                           BillSelected,
                           View):
    def post(self, request, pk):
        proformabill_item = get_object_or_404(
            self.model, bill=self.bill, pk=pk)

        def accept_qty(val):
            val = Decimal(val)
            if val < 0:
                raise Exception("Invalid QTY")
            return val

        def accept_new_total(val):
            if not val:
                val = proformabill_item.base_total_sin_impuestos
            val = Decimal(val)
            if not (val <= proformabill_item.base_total_sin_impuestos):
                val = proformabill_item.base_total_sin_impuestos
            if val < 0:
                raise Exception("Invalid discount")
            if val < proformabill_item.base_total_sin_impuestos - proformabill_item.max_discount:
                raise Exception("Invalid discount")
            return (proformabill_item.base_total_sin_impuestos - val).quantize(Decimal("0.01"))

        success = False
        for field, fun in [('qty', accept_qty),
                           ('discount', accept_new_total)]:
            try:
                val = request.POST[field]
                setattr(proformabill_item, field, fun(val))
                success = True
            except KeyError:
                pass
        proformabill_item.full_clean()
        if proformabill_item.qty == 0:
            proformabill_item.delete()
        else:
            proformabill_item.save()
        if success:
            return HttpResponse("Ok")
        else:
            return HttpResponse("No changes")


class BillItemDeleteView(BillItemView,
                         BillSelected,
                         DeleteView):
    """
    Delete view for proformabill items
    """


class BillListView(BillView, CompanySelected, ListView):
    context_object_name = "bill_list"

    @property
    def company_id(self):
        return self.kwargs['company_id']
