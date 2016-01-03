import pytz

from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic.list import ListView
from django.core.urlresolvers import reverse

import models
import forms
from company_accounts.views import CompanySelected


tz = pytz.timezone('America/Guayaquil')


class CustomerView(object):
    """
    Base class for an Customer View
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

    def get_queryset(self):
        return self.model.objects.filter(company=self.company).exclude(identificacion='9999999999999')


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
    @property
    def success_url(self):
        view_name = "{}_index".format(self.context_object_name)
        return reverse(view_name, args=(self.company.id, ))
