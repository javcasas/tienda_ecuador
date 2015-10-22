from django.conf.urls import patterns, url
from company_accounts import views

urlpatterns = patterns(
    '',
    # Index views
    url(r'^$',
        views.company_select, name='company_select'),
    url(r'^(?P<pk>[0-9]+)/$',
        views.CompanyProfileView.as_view(
            template_name_suffix='_main_menu'
        ), name='company_main_menu'),
    url(r'^(?P<pk>[0-9]+)/profile/$',
        views.CompanyProfileView.as_view(), name='company_profile'),
    url(r'^(?P<pk>[0-9]+)/profile/edit/$',
        views.CompanyProfileUpdateView.as_view(), name='company_profile_update'),
    url(r'^(?P<pk>[0-9]+)/profile/select_plan/$',
        views.CompanyProfileSelectPlanView.as_view(), name='company_profile_select_plan'),
    url(r'^(?P<pk>[0-9]+)/cert/$',
        views.CompanyUploadCertView.as_view(), name='company_upload_cert'),
)
