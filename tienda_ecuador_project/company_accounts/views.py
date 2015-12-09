from datetime import date, timedelta
import pytz
import json

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.generic import View
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, UpdateView, FormView
from django.core.urlresolvers import reverse
from django.db.models import Count

import models
import forms
from licence_helpers import LicenceControlMixin, valid_licence, licence_required
from util import signature
from util.sri_models import AmbienteSRI


tz = pytz.timezone('America/Guayaquil')


class LoggedInIndexView(View):
    def get(self, request):
        try:
            c_user = models.CompanyUser.objects.get(user=request.user)
            return redirect("company_accounts:company_main_menu", c_user.company.id)
        except (models.CompanyUser.DoesNotExist):
            return redirect("company_accounts:create_company")


class CompanyCreateView(CreateView):
    template_name_suffix = '_create_form'
    model = models.Company
    form_class = forms.CompanyForm

    def get(self, request):
        try:
            c_user = models.CompanyUser.objects.get(user=request.user)
            return redirect("company_accounts:company_main_menu", c_user[0].company.id)
        except (models.CompanyUser.DoesNotExist):
            return super(CompanyCreateView, self).get(request)

    def form_valid(self, form):
        """
        Creates a CompanyUser, default Establecimiento and PuntoEmision
        """
        # Delete orphaned CompanyUsers
        (models.Company.objects.annotate(number_of_companies=Count("companyuser"))
                               .filter(number_of_companies=0).delete())
        res = super(self.__class__, self).form_valid(form)
        new_company = form.instance
        # Create CompanyUser
        c_u = models.CompanyUser(user=self.request.user, company=new_company)
        c_u.save()
        # Create Establecimiento
        e = models.Establecimiento(
            company=new_company,
            descripcion=u'Matriz',
            codigo='001',
            direccion=new_company.direccion_matriz)
        e.save()
        # Create PuntoEmision
        pe = models.PuntoEmision(
            establecimiento=e,
            descripcion='Caja Principal',
            codigo='001',
            ambiente_sri=AmbienteSRI.options.produccion)
        pe.save()
        return res


def company_create(request):
    """
    If the user has a company, it redirects to the main menu, otherwise
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
        single_punto_emision = models.PuntoEmision.objects.filter(
            establecimiento__company=self.company)
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


class CompanyProfileView(CompanyView, CompanySelected, LicenceControlMixin, DetailView):
    """
    View that shows a general index for a given company
    """


class CompanyProfileUpdateView(CompanyView, CompanySelected, UpdateView):
    """
    View that shows a general index for a given company
    """
    form_class = forms.CompanyForm
    def form_valid(self, form):
        res = super(CompanyProfileUpdateView, self).form_valid(form)
        new_company = form.instance
        # Actualizar direccion del establecimiento matriz
        for e in self.company.establecimientos.filter(descripcion='Matriz'):
            e.direccion = new_company.direccion_matriz
            e.save()
        return res


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


class CompanyPayLicenceView(CompanyView, CompanySelected, LicenceControlMixin, DetailView):
    """
    View that shows a general index for a given company
    """
    template_name_suffix = '_pay_licence'

    def get_context_data(self, **kwargs):
        res = super(CompanyPayLicenceView, self).get_context_data(**kwargs)
        res['licence_name'] = unicode(self.company.licence).capitalize()
        res['price_to_pay'] = {
            'basic': 29,
            'professional': 69,
            'enterprise': 295,
        }[self.company.licence.licence]
        return res

    def post(self, request, **kwargs):
        data = request.POST
        try:
            assert data['payment_method'] == 'western_union'
            payment = models.LicenceUpdateRequest(
                licence=self.company.licence,
                date=date.today(),
                action=json.dumps({
                    'payment_method': data['payment_method'],
                    'sender_name': data['sender_name'],
                    'sender_code': data['sender_code'],
                    'new_licence': self.company.licence.next_licence,
                }))
            payment.save()
            l = self.company.licence
            if l.expired:
                l.approve(l.next_licence, date.today() + timedelta(days=30))
            else:
                l.approve(l.next_licence, l.expiration + timedelta(days=30))
            return redirect("company_accounts:company_profile", self.company.id)
        except AssertionError:
            pass
        except ValueError:
            return self.get(request, **kwargs)

        return self.get(request)


#########################
# Establecimiento views #
#########################
class EstablecimientoView(object):
    model = models.Establecimiento
    context_object_name = 'establecimiento'

    @property
    def establecimiento_id(self):
        return self.kwargs["pk"]


class EstablecimientoDetailView(EstablecimientoView, EstablecimientoSelected, DetailView):
    """
    """


class EstablecimientoUpdateView(EstablecimientoView, EstablecimientoSelected, UpdateView):
    """
    """
    form_class = forms.EstablecimientoForm


######################
# PuntoEmision views #
######################
class PuntoEmisionView(object):
    model = models.PuntoEmision
    context_object_name = 'punto_emision'

    @property
    def punto_emision_id(self):
        return self.kwargs["pk"]


class PuntoEmisionDetailView(PuntoEmisionView, PuntoEmisionSelected, DetailView):
    """
    View that shows a general index for a given punto_emision
    """


class PuntoEmisionUpdateView(PuntoEmisionView, PuntoEmisionSelected, UpdateView):
    """
    View that shows a general index for a given punto_emision
    """
    form_class = forms.PuntoEmisionForm
