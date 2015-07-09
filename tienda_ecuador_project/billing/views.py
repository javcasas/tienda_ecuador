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
class ItemView(RequiresCompany):
    """
    Base class for an Item View
    """
    model = Item

    def get_queryset(self):
        return self.model.objects.filter(company=self.company)


class ItemListView(ItemView, ListView):
    context_object_name = "item_list"

    def get_context_data(self, **kwargs):
        context = super(ItemListView, self).get_context_data(**kwargs)
        context['item_list'] = Item.objects.filter(company=self.company)
        context['company'] = self.company
        return context


class ItemListViewJson(JSONResponseMixin, ItemListView):
    def render_to_response(self, context, **response_kwargs):
        return self.render_to_json_response(context, **response_kwargs)


class ItemDetailView(ItemView, DetailView):
    context_object_name = 'item'

    def get_context_data(self, **kwargs):
        context = super(self.__class__, self).get_context_data(**kwargs)
        context['company'] = self.company
        return context


class ItemCreateView(ItemView, CreateView):
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

    def form_invalid(self, form):
        response = super(self.__class__, self).form_invalid(form)
        self.company
        return response


class ItemUpdateView(ItemView, UpdateView):
    fields = ['sku', 'name', 'description', 'vat_percent', 'unit_cost', 'unit_price']
    context_object_name = 'item'
    form_class = ItemForm

    def get_context_data(self, **kwargs):
        context = super(self.__class__, self).get_context_data(**kwargs)
        context['company'] = self.company
        return context


class ItemDeleteView(ItemView, DeleteView):
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
class CustomerView(RequiresCompany):
    """
    Base class for an Item View
    """
    model = Customer

    def get_queryset(self):
        return self.model.objects.filter(company=self.company)


class CustomerListView(CustomerView, ListView):
    context_object_name = "customer_list"

    def get_context_data(self, **kwargs):
        context = super(self.__class__, self).get_context_data(**kwargs)
        context['company'] = self.company
        return context


class CustomerDetailView(CustomerView, DetailView):
    context_object_name = 'customer'

    def get_context_data(self, **kwargs):
        context = super(self.__class__, self).get_context_data(**kwargs)
        context['company'] = self.company
        return context


class CustomerCreateView(CustomerView, CreateView):
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


class CustomerUpdateView(CustomerView, UpdateView):
    fields = ['name', ]
    context_object_name = 'customer'
    form_class = CustomerForm

    def get_context_data(self, **kwargs):
        context = super(self.__class__, self).get_context_data(**kwargs)
        context['company'] = self.company
        return context


class CustomerDeleteView(CustomerView, DeleteView):
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
class ProformaBillView(RequiresCompany):
    model = ProformaBill

    def get_queryset(self):
        return self.model.objects.filter(company=self.company)


class ProformaBillListView(ProformaBillView, ListView):
    context_object_name = "proformabill_list"

    def get_context_data(self, **kwargs):
        context = super(self.__class__, self).get_context_data(**kwargs)
        context['company'] = self.company
        return context


class ProformaBillDetailView(ProformaBillView, DetailView):
    context_object_name = 'proformabill'

    def get_context_data(self, **kwargs):
        context = super(self.__class__, self).get_context_data(**kwargs)
        context['company'] = self.company
        return context


class ProformaBillCreateView(ProformaBillView, CreateView):
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


class ProformaBillUpdateView(ProformaBillView, UpdateView):
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


class ProformaBillDeleteView(ProformaBillView, DeleteView):
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


#############################################################
#   Proforma Bill Item views
#############################################################
class ProformaBillAddItemView(RequiresCompany, ProformaBillSelected, CreateView):
    model = ProformaBillItem
    fields = ['sku', 'name', 'description', ]
    context_object_name = 'item'
    template_name_suffix = '_create_form'
    form_class = ProformaBillAddItemForm

    def get_context_data(self, **kwargs):
        context = super(self.__class__, self).get_context_data(**kwargs)
        context['company'] = self.company
        context['proformabill'] = self.proformabill
        return context

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

    def get_success_url(self):
        return reverse("proformabill_detail", args=(self.company.id, self.proformabill.id))


class ProformaBillItemUpdateView(RequiresCompany, ProformaBillSelected, UpdateView):
    model = ProformaBillItem
    context_object_name = 'item'
    template_name_suffix = '_form'
    form_class = ProformaBillItemForm

    def get_context_data(self, **kwargs):
        context = super(self.__class__, self).get_context_data(**kwargs)
        context['company'] = self.company
        context['proformabill'] = self.proformabill
        return context

    def form_valid(self, form):
        form.instance.proforma_bill = self.proformabill
        return super(self.__class__, self).form_valid(form)

    def get_success_url(self):
        return reverse("proformabill_detail", args=(self.company.id, self.proformabill.id))


class ProformaBillItemDeleteView(RequiresCompany, ProformaBillSelected, DeleteView):
    context_object_name = 'item'
    model = ProformaBillItem

    @property
    def success_url(self):
        return reverse("proformabill_detail", args=(self.company.id, self.proformabill.id))

    def get_context_data(self, **kwargs):
        context = super(self.__class__, self).get_context_data(**kwargs)
        context['company'] = self.company
        return context
