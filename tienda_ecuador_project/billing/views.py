import tempfile
import os
import base64
import pytz
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
from django.utils.decorators import method_decorator


import models
from models import (Item,
                    Bill,
                    CompanyUser,
                    Company,
                    Customer,
                    ProformaBill,
                    ProformaBillItem,
                    Establecimiento,
                    PuntoEmision,
                    ClaveAcceso)
from forms import (ItemForm,
                   ProformaBillForm,
                   ProformaBillAddItemForm,
                   ProformaBillItemForm,
                   CustomerForm)

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


def valid_licence(user, valid_licences):
    cu = get_object_or_404(models.CompanyUser, user=user)
    return cu.company.licencia in valid_licences


class licence_required(object):
    def __init__(self, *args):
        self.licences = args

    def __call__(self, f):
        orig_dispatch = f.dispatch
        def wrapper(otherself, request, *args, **kwargs):
            if not valid_licence(request.user, self.licences):
                return redirect("pricing")
            return orig_dispatch(otherself, request, *args, **kwargs)
        f.dispatch = wrapper
        return f


class LicenceControlMixin(object):
    def valid_licence(self, valid_licences):
        return valid_licence(self.user, valid_licences)
    def get_context_data(self, **kwargs):
        context = super(CompanySelected, self).get_context_data(**kwargs)
        licence = get_object_or_404(models.CompanyUser, user=user).company.licencia
        context['licence'] = {licence: True}
        return context


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
        single_punto_emision = PuntoEmision.objects.filter(establecimiento__company=self.company)
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
            'item_list': Item.objects.filter(company=company).order_by('sku')[:5],
            'bill_list': Bill.objects.filter(company=company),
            'proformabill_list': ProformaBill.objects.filter(punto_emision__establecimiento__company=company).order_by("number")[:5],
            'customer_list': Customer.objects.filter(company=company).order_by('identificacion')[:5],
            'company': company,
            'single_punto_emision': self.single_punto_emision,
            'user': self.request.user,
        })
        return render(request, "billing/company_index.html", context)

class CompanyProfileView(CompanySelected, DetailView):
    """
    View that shows a general index for a given company
    """
    model = models.Company
    context_object_name = 'company'
    @property
    def company_id(self):
        """
        Overridable property to get the current company id
        """
        return self.kwargs['pk']

class CompanyProfileUpdateView(CompanySelected, DetailView):
    """
    View that shows a general index for a given company
    """
    model = models.Company
    context_object_name = 'company'

class CompanyProfileSelectPlanView(CompanySelected, View):
    """
    View that shows a general index for a given company
    """
    model = models.Company
    context_object_name = 'company'

    @property
    def company_id(self):
        """
        Overridable property to get the current company id
        """
        return self.kwargs['pk']

    def get(self, request, pk):
        context = {
            'company': self.company,
            'select_urls': [
                {'name': 'basic'},
                {'name': 'professional'},
                {'name': 'enterprise'},
            ],
        }
        return render(request, "billing/company_profile_select_plan.html", context)

    def post(self, request, pk):
        try:
            plan = request.POST['selected_plan']
            company = self.company
            company.licencia = plan
            company.full_clean()
            company.save()
            return redirect('company_profile', company.id)
        except Exception, e:
            print e
            return self.get(request, pk)


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
        return self.model.objects.filter(punto_emision__establecimiento__company=self.company)

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
        #elif request.POST['payment_mode'] == 'installments':
            #return HttpResponse(str(("Cuotitas", request.POST['payment_method'], request.POST['payment_installments'], request.POST['payment_time_between_installments'])))
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


class ProformaBillUpdateView(ProformaBillView, PuntoEmisionSelected, UpdateView):
    form_class = ProformaBillForm

    def get_form(self, *args, **kwargs):
        form = super(self.__class__, self).get_form(*args, **kwargs)
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

    def post(self, request, pk):
        proforma = self.get_object()
        if proforma.secuencial == 0:
            proforma.secuencial = proforma.punto_emision.siguiente_secuencial
            proforma.punto_emision.siguiente_secuencial += 1
        proforma.save()
        proforma.punto_emision.save()
        return HttpResponse("ok")


@licence_required('basic', 'professional', 'enterprise')
class ProformaBillEmitGenXMLView(ProformaBillView,
                                 PuntoEmisionSelected,
                                 DetailView):
    template_name_suffix = '_xml'

    def get_context_data(self, **kwargs):
        context = super(self.__class__, self).get_context_data(**kwargs)

        info_tributaria = {}
        info_tributaria['ambiente'] = {
            'pruebas': '1',
            'produccion': '2'
        }[self.company.ambiente_sri]

        info_tributaria['tipo_emision'] = '1'   # 1: normal
                                                # 2: indisponibilidad sistema
        info_tributaria['cod_doc'] = '01'   # 01: factura
                                            # 04: nota de credito
                                            # 05: nota de debito
                                            # 06: guia de remision
                                            # 07: comprobante de retencion
        proformabill = context['proformabill']

        c = ClaveAcceso()
        proformabill.date = proformabill.date.astimezone(
            pytz.timezone('America/Guayaquil'))
        c.fecha_emision = (proformabill.date.year,
                           proformabill.date.month,
                           proformabill.date.day)
        c.tipo_comprobante = "factura"
        c.ruc = str(self.company.ruc)
        c.ambiente = self.company.ambiente_sri
        c.serie = 23013   # FIXME
        c.numero = proformabill.secuencial
        c.codigo = 17907461  # FIXME
        c.tipo_emision = "normal"
        info_tributaria['clave_acceso'] = unicode(c)

        context['info_tributaria'] = info_tributaria

        info_factura = {}
        info_factura['tipo_identificacion_comprador'] = {    # tabla 7
            'ruc': '04',
            'cedula': '05',
            'pasaporte': '06',
            'consumidor_final': '07',
            'exterior': '08',
            'placa': '09',
        }[context['proformabill'].issued_to.tipo_identificacion]
        info_factura['total_descuento'] = 0     # No hay descuentos
        info_factura['propina'] = 0             # No hay propinas
        info_factura['moneda'] = 'DOLAR'
        context['info_factura'] = info_factura
        return context

    def render_to_response(self, context, **kwargs):
        res = super(self.__class__, self).render_to_response(context, **kwargs)
        res.render()
        xml_content = res.content
        # sign xml_content
        d = tempfile.mkdtemp()
        try:
            cert_path = os.path.join(d, "cert")
            xml_path = os.path.join(d, "xml")
            with open(cert_path, "w") as f:
                f.write(base64.b64decode(self.company.cert))
            with open(xml_path, "w") as f:
                f.write(xml_content)
            os.system(
                'cd {signer_dir} && '
                'java'
                ' -classpath "core/*:deps/*:./sources/MITyCLibXADES/test/:."'
                ' XAdESBESSignature'
                ' {xml_path} {keystore_path} {keystore_pw}'
                ' {res_dir} xml_signed'.format(
                    signer_dir='billing/signer/',
                    xml_path=xml_path,
                    keystore_path=cert_path,
                    keystore_pw=self.company.key,
                    res_dir=d))
            xml_content = open(os.path.join(d, "xml_signed")).read()
        except IOError:
            # Failure to sign
            raise
        finally:
            for f in os.listdir(d):
                os.unlink(os.path.join(d, f))
            os.rmdir(d)

        res.content = xml_content
        return res


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
        copy_from = Item.objects.filter(company=self.company).get(id=copy_from.id)
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
        proformabill_item = get_object_or_404(self.model, proforma_bill=self.proformabill, pk=pk)

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
class BillView(CompanySelected):
    model = Bill
    context_object_name = 'bill'

    def get_queryset(self):
        return self.model.objects.filter(company=self.company)

    @property
    def punto_emision_id(self):
        return self.model.objects.get(id=self.kwargs['pk']).punto_emision.id


class BillDayListReport(BillView, ListView):
    context_object_name = "bill_list"

    def get_queryset(self):
        start_date = datetime(int(self.kwargs['year']),
                              int(self.kwargs['month']),
                              int(self.kwargs['day']))
        end_date = start_date + timedelta(days=1)
        return self.model.objects.filter(company=self.company).filter(date__gte=start_date, date__lt=end_date)

    def get_context_data(self, **kwargs):
        context = super(BillDayListReport, self).get_context_data(**kwargs)
        for key in ['year', 'month', 'day']:
            context[key] = self.kwargs[key]
        return context
