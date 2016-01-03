from django.conf.urls import patterns, url
from company_accounts import views, forms
from django.contrib.auth.decorators import login_required

urlpatterns = [
    # Index views
    url(r'^$',
        login_required(views.LoggedInIndexView.as_view()), name='company_select'),

    # Company Views
    url(r'^new/$',
        login_required(views.CompanyCreateView.as_view()), name='create_company'),
    url(r'^(?P<pk>[0-9]+)/$',
        views.CompanyProfileView.as_view(
            template_name_suffix='_main_menu'
        ), name='company_main_menu'),
    url(r'^(?P<pk>[0-9]+)/profile/$',
        views.CompanyProfileView.as_view(), name='company_profile'),
    url(r'^(?P<pk>[0-9]+)/profile/edit/$',
        views.CompanyProfileUpdateView.as_view(), name='company_profile_update'),
    url(r'^(?P<pk>[0-9]+)/profile/edit_logo/$',
        views.CompanyProfileUpdateView.as_view(
            form_class=forms.CompanyLogoForm
        ), name='company_profile_update_logo'),
    url(r'^(?P<pk>[0-9]+)/profile/select_plan/$',
        views.CompanyProfileSelectPlanView.as_view(), name='company_profile_select_plan'),
    url(r'^(?P<pk>[0-9]+)/cert/$',
        views.CompanyUploadCertView.as_view(), name='company_upload_cert'),

    url(r'^(?P<pk>[0-9]+)/pay_licence/$',
        views.CompanyPayLicenceView.as_view(), name='pay_licence'),

    # Company Structure view
    url(r'^(?P<pk>[0-9]+)/structure/$',
        views.CompanyProfileView.as_view(
            template_name_suffix='_structure'
        ), name='company_structure'),

    # Establecimiento Views
    url(r'^establecimiento/(?P<pk>[0-9]+)/$',
        views.EstablecimientoDetailView.as_view(), name='establecimiento_detail'),
    url(r'^establecimiento/(?P<pk>[0-9]+)/edit/$',
        views.EstablecimientoUpdateView.as_view(), name='establecimiento_update'),

    # PuntoEmision Views
    url(r'^punto_emision/(?P<pk>[0-9]+)/$',
        views.PuntoEmisionDetailView.as_view(), name='punto_emision_detail'),
    url(r'^punto_emision/(?P<pk>[0-9]+)/edit/$',
        views.PuntoEmisionUpdateView.as_view(), name='punto_emision_update'),
]
