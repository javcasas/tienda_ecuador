import tempfile
import os
import base64
import pytz

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.generic import View
from django.views.generic.list import ListView
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.core.urlresolvers import reverse
from django.http import JsonResponse
from django.forms.models import model_to_dict

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
        return context


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
        context = {
            'item_list': Item.objects.filter(company=company),
            'bill_list': [], # FIXME Bill.objects.filter(company=company),
            'proformabill_list': ProformaBill.objects.filter(punto_emision__establecimiento__company=company),
            'customer_list': Customer.objects.filter(company=company),
            'company': company,
        }
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

    def form_valid(self, form):
        form.instance.company = self.company
        return super(ItemCreateView, self).form_valid(form)


class ItemUpdateView(ItemView, CompanySelected, UpdateView):
    form_class = ItemForm


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
    fields = ['name', ]
    template_name_suffix = '_create_form'
    form_class = CustomerForm

    def form_valid(self, form):
        form.instance.company = self.company
        return super(self.__class__, self).form_valid(form)


class CustomerUpdateView(CustomerView, CompanySelected, UpdateView):
    fields = ['name', ]
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


class ProformaBillCreateView(PuntoEmisionSelected,
                             ProformaBillView,
                             CreateView):
    fields = ['number', 'issued_to', 'date']
    template_name_suffix = '_create_form'
    form_class = ProformaBillForm

    def get_form(self, *args, **kwargs):
        form = super(self.__class__, self).get_form(*args, **kwargs)
        form.fields['issued_to'].queryset = Customer.objects.filter(
            company=self.company)
        return form

    def form_valid(self, form):
        form.instance.company = self.company
        form.instance.punto_emision = self.punto_emision
        return super(self.__class__, self).form_valid(form)


class ProformaBillUpdateView(ProformaBillView, PuntoEmisionSelected, UpdateView):
    fields = ['number', ]
    form_class = ProformaBillForm

    def get_form(self, *args, **kwargs):
        form = super(self.__class__, self).get_form(*args, **kwargs)
        form.fields['issued_to'].queryset = Customer.objects.filter(
            company=self.company)
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
class ProformaBillEmitView(ProformaBillView, PuntoEmisionSelected, DetailView):
    template_name_suffix = '_emit'


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
        info_tributaria['secuencial'] = {
            'pruebas': self.company.siguiente_comprobante_pruebas,
            'produccion': self.company.siguiente_comprobante_produccion,
        }[self.company.ambiente_sri]

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
        c.numero = info_tributaria['secuencial']
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
    fields = ['sku', 'name', 'description', ]
    template_name_suffix = '_create_form'
    form_class = ProformaBillAddItemForm

    def get_form(self, *args, **kwargs):
        form = super(self.__class__, self).get_form(*args, **kwargs)
        form.fields['copy_from'].queryset = Item.objects.filter(
            company=self.company)
        if form.data.get('copy_from'):
            form.data = form.data.copy()
            form.data['proforma_bill'] = self.proformabill.id
            copy_from = Item.objects.get(pk=form.data['copy_from'])
            for field in form.Meta.fields:
                if field in ['qty']:
                    continue
                fieldval = getattr(copy_from, field)
                try:
                    form.data[field] = fieldval.id
                except AttributeError:
                    form.data[field] = fieldval
        return form

    def form_valid(self, form):
        form.instance.proforma_bill = self.proformabill
        to_search = form.cleaned_data.copy()
        to_search.pop("copy_from")
        to_search.pop('qty')
        current_item = ProformaBillItem.objects.filter(**to_search)
        if current_item:
            form.instance.id = current_item[0].id
            form.instance.qty = current_item[0].qty + form.instance.qty
        return super(self.__class__, self).form_valid(form)


class ProformaBillItemUpdateView(ProformaBillItemView,
                                 ProformaBillSelected,
                                 UpdateView):
    template_name_suffix = '_form'
    form_class = ProformaBillItemForm

    def form_valid(self, form):
        form.instance.proforma_bill = self.proformabill
        return super(self.__class__, self).form_valid(form)


class ProformaBillItemDeleteView(ProformaBillItemView,
                                 ProformaBillSelected,
                                 DeleteView):
    """
    Delete view for proformabill items
    """
