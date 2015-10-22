from datetime import date
import pytz

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.generic import View
from django.views.generic.list import ListView
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, UpdateView, DeleteView, FormView
from django.core.urlresolvers import reverse, reverse_lazy

import models
import forms
from licence_helpers import LicenceControlMixin, valid_licence, licence_required
from util import signature


tz = pytz.timezone('America/Guayaquil')


@login_required
def company_select(request):
    """
    Shows an index for the current user,
    showing the companies he can administer
    If there is a single company,
    it redirects to the company automatically
    """
    request.current_app = request.resolver_match.namespace
    c_user = models.CompanyUser.objects.filter(user=request.user)
    if len(c_user) == 1:
        return redirect("company_accounts:company_main_menu", c_user[0].company.id)
    param_dict = {
        'companies':
            models.Company.objects.filter(id__in=[cu.id for cu in c_user]),
        'user': request.user,
    }
    return render(request, "company_accounts/index.html", param_dict)


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
            models.CompanyUser,
            user_id=self.request.user.id, company_id=self.company_id)
        return get_object_or_404(models.Company, id=self.company_id)

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
        single_punto_emision = models.PuntoEmision.objects.filter(establecimiento__company=self.company)
        if len(single_punto_emision) == 1:
            return single_punto_emision[0]
        else:
            return None


class EstablecimientoSelected(CompanySelected):
    @property
    def establecimiento(self):
        return get_object_or_404(
            models.Establecimiento,
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
            models.PuntoEmision,
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


###############################
# Company Profile Views
###############################
class CompanyView(object):
    model = models.Company
    context_object_name = 'company'

    @property
    def company_id(self):
        """
        Overridable property to get the current company id
        """
        return self.kwargs['pk']


class CompanyProfileView(CompanyView, CompanySelected, DetailView):
    """
    View that shows a general index for a given company
    """



class CompanyProfileUpdateView(CompanyView, CompanySelected, UpdateView):
    """
    View that shows a general index for a given company
    """
    form_class = forms.CompanyForm


class CompanyProfileSelectPlanView(CompanyView, CompanySelected, View):
    """
    View that shows a general index for a given company
    """

    def get(self, request, pk):
        context = {
            'company': self.company,
            'select_urls': [
                {'name': 'basic'},
                {'name': 'professional'},
                {'name': 'enterprise'},
            ],
        }
        return render(request, "company_accounts/company_profile_select_plan.html", context)

    def post(self, request, pk):
        try:
            plan = request.POST['selected_plan']
            company = self.company
            company.licence.next_licence = plan
            if company.licence.effective_licence == 'demo':
                company.licence.approve(plan, date(2010, 1, 1))
            company.licence.save()
            return redirect('company_accounts:company_profile', company.id)
        except Exception, e:
            print e
            return self.get(request, pk)


class CompanyUploadCertView(CompanyView, CompanySelected, FormView):
    """
    View that shows a general index for a given company
    """
    template_name = "company_accounts/company_upload_cert.html"
    form_class = forms.CertificateForm

    @property
    def success_url(self):
        return reverse("company_accounts:company_profile", args=(self.company.id,))

    def form_valid(self, form):
        cert_key = form.cleaned_data['cert_key']
        cert_data = form.cleaned_data['cert_data']
        signature.add_cert(self.company.ruc, self.company.id, cert_data, cert_key)
        return super(CompanyUploadCertView, self).form_valid(form)
