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
                    ProformaBillItem)
from forms import (ItemForm,
                   ProformaBillForm,
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


class RequiresCompany(object):
    """
    Class that offers the self.company attribute.
    The attribute checks that the company exists, or 404
    """
    @classmethod
    def as_view(cls, **initkwargs):
        view = super(RequiresCompany, cls).as_view(**initkwargs)
        return login_required(view)

    def check_has_access_to_company(self):
        company_id = self.kwargs['company_id']
        get_object_or_404(
            CompanyUser, user__id=self.request.user.id, company_id=company_id)

    @property
    def company(self):
        company_id = self.kwargs['company_id']
        self.check_has_access_to_company()
        return get_object_or_404(Company, id=company_id)


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
        return map(model_to_dict, list(self.model.objects.filter(company=self.company)))


class CompanyIndex(RequiresCompany, View):
    def get(self, request, company_id):
        """
        Shows an index for a company
        """
        company = self.company
        context = {
            'item_list': Item.objects.filter(company=company),
            'bill_list': Bill.objects.filter(company=company),
            'proformabill_list': ProformaBill.objects.filter(company=company),
            'customer_list': Customer.objects.filter(company=company),
            'company': self.company,
        }
        return render(request, "billing/company_index.html", context)


####################################################################
#   Item views
####################################################################

class ItemListView(RequiresCompany, ListView):
    model = Item
    context_object_name = "item_list"

    def get_context_data(self, **kwargs):
        context = super(ItemListView, self).get_context_data(**kwargs)
        context['item_list'] = Item.objects.filter(company=self.company)
        context['company'] = self.company
        return context


class ItemListViewJson(JSONResponseMixin, ItemListView):
    def render_to_response(self, context, **response_kwargs):
        return self.render_to_json_response(context, **response_kwargs)


class ItemDetailView(RequiresCompany, DetailView):
    model = Item
    context_object_name = 'item'

    def get_context_data(self, **kwargs):
        context = super(self.__class__, self).get_context_data(**kwargs)
        context['company'] = self.company
        return context


class ItemCreateView(RequiresCompany, CreateView):
    model = Item
    fields = ['sku', 'name', 'description', 'vat_percent', 'unit_cost', 'unit_price']
    context_object_name = 'item'
    template_name_suffix = '_create_form'
    form_class = ItemForm

    def get_context_data(self, **kwargs):
        context = super(self.__class__, self).get_context_data(**kwargs)
        context['company'] = self.company
        return context

    def form_valid(self, form):
        form.instance.company = self.company
        return super(ItemCreateView, self).form_valid(form)


class ItemUpdateView(RequiresCompany, UpdateView):
    model = Item
    fields = ['sku', 'name', 'description', 'vat_percent', 'unit_cost', 'unit_price']
    context_object_name = 'item'
    form_class = ItemForm

    def get_context_data(self, **kwargs):
        context = super(self.__class__, self).get_context_data(**kwargs)
        context['company'] = self.company
        return context


class ItemDeleteView(RequiresCompany, DeleteView):
    model = Item
    context_object_name = 'item'

    @property
    def success_url(self):
        return reverse("item_index", args=(self.company.id, ))

    def get_context_data(self, **kwargs):
        context = super(self.__class__, self).get_context_data(**kwargs)
        context['company'] = self.company
        return context


####################################################################
#   Customer views
####################################################################

class CustomerListView(RequiresCompany, ListView):
    model = Customer
    context_object_name = "customer_list"

    def get_context_data(self, **kwargs):
        context = super(self.__class__, self).get_context_data(**kwargs)
        context['customer_list'] = self.model.objects.filter(
            company=self.company)
        context['company'] = self.company
        return context


class CustomerDetailView(RequiresCompany, DetailView):
    model = Customer
    context_object_name = 'customer'

    def get_context_data(self, **kwargs):
        context = super(self.__class__, self).get_context_data(**kwargs)
        context['company'] = self.company
        return context


class CustomerCreateView(RequiresCompany, CreateView):
    model = Customer
    fields = ['name', ]
    context_object_name = 'customer'
    template_name_suffix = '_create_form'
    form_class = CustomerForm

    def get_context_data(self, **kwargs):
        context = super(self.__class__, self).get_context_data(**kwargs)
        context['company'] = self.company
        return context

    def form_valid(self, form):
        form.instance.company = self.company
        return super(self.__class__, self).form_valid(form)


class CustomerUpdateView(RequiresCompany, UpdateView):
    model = Customer
    fields = ['name', ]
    context_object_name = 'customer'
    form_class = CustomerForm

    def get_context_data(self, **kwargs):
        context = super(self.__class__, self).get_context_data(**kwargs)
        context['company'] = self.company
        return context


class CustomerDeleteView(RequiresCompany, DeleteView):
    model = Customer
    context_object_name = 'customer'

    @property
    def success_url(self):
        view_name = "{}_index".format(self.context_object_name)
        return reverse(view_name, args=(self.company.id, ))

    def get_context_data(self, **kwargs):
        context = super(self.__class__, self).get_context_data(**kwargs)
        context['company'] = self.company
        return context


#############################################################
#   Proforma Bill views
#############################################################

class ProformaBillListView(RequiresCompany, ListView):
    model = ProformaBill
    context_object_name = "proformabill_list"

    def get_context_data(self, **kwargs):
        context = super(self.__class__, self).get_context_data(**kwargs)
        context['proformabill_list'] = self.model.objects.filter(
            company=self.company)
        context['company'] = self.company
        return context


class ProformaBillDetailView(RequiresCompany, DetailView):
    model = ProformaBill
    context_object_name = 'proformabill'

    def get_context_data(self, **kwargs):
        context = super(self.__class__, self).get_context_data(**kwargs)
        context['company'] = self.company
        return context


class ProformaBillCreateView(RequiresCompany, CreateView):
    model = ProformaBill
    fields = ['number', 'issued_to', 'date']
    context_object_name = 'proformabill'
    template_name_suffix = '_create_form'
    form_class = ProformaBillForm

    def get_context_data(self, **kwargs):
        context = super(self.__class__, self).get_context_data(**kwargs)
        context['company'] = self.company
        return context

    def get_form(self, *args, **kwargs):
        form = super(self.__class__, self).get_form(*args, **kwargs)
        form.fields['issued_to'].queryset = Customer.objects.filter(
            company=self.company)
        return form

    def form_valid(self, form):
        form.instance.company = self.company
        print form.errors
        return super(self.__class__, self).form_valid(form)


class ProformaBillUpdateView(RequiresCompany, UpdateView):
    model = ProformaBill
    fields = ['number', ]
    context_object_name = 'proformabill'
    form_class = ProformaBillForm

    def get_context_data(self, **kwargs):
        context = super(self.__class__, self).get_context_data(**kwargs)
        context['company'] = self.company
        return context

    def get_form(self, *args, **kwargs):
        form = super(self.__class__, self).get_form(*args, **kwargs)
        form.fields['issued_to'].queryset = Customer.objects.filter(
            company=self.company)
        return form


class ProformaBillDeleteView(RequiresCompany, DeleteView):
    model = ProformaBill
    context_object_name = 'proformabill'

    @property
    def success_url(self):
        view_name = "{}_index".format(self.context_object_name)
        return reverse(view_name, args=(self.company.id, ))

    def get_context_data(self, **kwargs):
        context = super(self.__class__, self).get_context_data(**kwargs)
        context['company'] = self.company
        return context

class ProformaBillSelected(object):
    @property
    def proformabill(self):
        proformabill_id = self.kwargs['proformabill_id']
        self.check_has_access_to_company()
        return get_object_or_404(ProformaBill, company=self.company, id=proformabill_id)


class ProformaBillAddItemView(RequiresCompany, ProformaBillSelected, CreateView):
    model = ProformaBillItem
    fields = ['sku', 'name', 'description', ]
    context_object_name = 'item'
    template_name_suffix = '_create_form'
    form_class = ProformaBillItemForm

    def get_context_data(self, **kwargs):
        context = super(self.__class__, self).get_context_data(**kwargs)
        context['company'] = self.company
        context['proformabill'] = self.proformabill
        return context

    def get_form(self, *args, **kwargs):
        form = super(self.__class__, self).get_form(*args, **kwargs)
        form.fields['copy_from'].queryset = Item.objects.filter(
            company=self.company)
        return form

    def form_valid(self, form):
        form.instance.company = self.company
        form.instance.proforma_bill = self.proformabill
        return super(self.__class__, self).form_valid(form)

    def get_success_url(self):
        return reverse("proformabill_detail", args=(self.company.id, self.proformabill.id))

class BillXmlView(object):
    class InfoTributaria(object):
        __slots__ = [
            'ambiente', 'tipo_emision', 'razon_social', 'nombre_comercial',
            'ruc', 'clave_acceso', 'cod_doc', 'establecimiento',
            'punto_emision', 'secuencial', 'direccion_matriz',
        ]
    class InfoFactura(object):
        __slots__ = [
            'fecha_emision', 'direccion_establecimiento',
            'contribuyente_especial', 'obligado_contabilidad',
            'tipo_identificacion_comprador', 'razon_social_comprador',
            'identificacion_comprador', 'total_sin_impuestos',
            'total_descuento', 'impuestos', 'propina', 'importe_total',
            'moneda',
        ]
        class TotalImpuestos(object):
            __slots__ = [
                'codigo', 'codigo_porcentaje', 'descuento_adicional'
                'base_imponible', 'valor'
            ]
    class Detalle(object):
        __slots__ = [
            'codigo_principal', 'codigo_auxiliar', 'descripcion',
            'unidad_medida', 'cantidad', 'precio_unitario', 'descuento',
            'total_sin_impuesto',
        ]
        class Impuesto(object):
            __slots__ = [
                'codigo', 'codigo_porcentaje', 'tarifa', 'base_imponible',
                'valor',
            ]
    class Retencion(object):
        __slots__ = [
                'codigo', 'codigo_porcentaje', 'tarifa', 'valor'
        ]
    
