from django.conf.urls import include, url
from django.contrib import admin
from django.views.generic import TemplateView
from django.conf.urls.static import static
from django.conf import settings
from django.contrib.auth.decorators import login_required
import views
import company_accounts.views
import company_accounts.forms


urlpatterns = [
    # Examples:
    url(r'^$', TemplateView.as_view(template_name='index.html'), name='home'),
    url(r'^request_info/$', views.RequestInfoView.as_view(template_name='request_info.html'), name='request_info'),
    url(r'^about/$', views.RedirectToIndexView.as_view(), name='about'),
    url(r'^benefits/$', TemplateView.as_view(template_name='benefits.html'), name='benefits'),
    url(r'^pricing/$', TemplateView.as_view(template_name='pricing.html'), name='pricing'),
    url(r'^support/$', views.SupportView.as_view(), name='support'),

    # Support forms
    url(r'^app_support/(?P<company_id>[0-9]+)/$', views.AppSupportView.as_view(), name='support_request_submit'),
    url(r'^app_support/success/$', TemplateView.as_view(
        template_name='support_request_completed.html'
    ), name='support_request_completed'),

    # Sales forms
    url(r'^sales_support/$', views.SalesSupportView.as_view(
        template_name='sales_form.html'
    ), name='sales_support'),
    url(r'^sales_support/success/$', TemplateView.as_view(
        template_name='sales_request_completed.html'
    ), name='sales_request_completed'),

    # General info pages
    url(r'^info/cert/$', TemplateView.as_view(
        template_name='info/certificate.html',
    ), name='info_cert'),
    url(r'^info/factura_electronica/$', TemplateView.as_view(
        template_name='info/factura_electronica.html',
    ), name='info_factura_electronica'),

    url(r'^admin/', include(admin.site.urls)),
    url(r'^comprobantes/', include('public_receipts.urls', namespace='public-receipts')),
    url(r'^company_accounts/',
        include('company_accounts.urls',
                app_name='company_accounts', namespace='company-accounts')),
    url(r'^stakeholders/',
        include('stakeholders.urls',)),
    url(r'^inventory/',
        include('inventory.urls',)),
    url(r'^purchases/',
        include('purchases.urls',)),
    url(r'^billing/', include('billing.urls')),
    url(r'^accounts_receivable/', include('accounts_receivable.urls')),
    url(r'^reports/', include('reports.urls')),

    url(r'^accounts/', include('registration.backends.simple.urls')),
    url(r'^accounts/register/complete$',
        login_required(company_accounts.views.LoggedInIndexView.as_view()),
        name='registration_complete'),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
