from django.conf.urls import include, url
from django.contrib import admin
from django.views.generic import TemplateView
from django.conf.urls.static import static
from django.conf import settings
import views
import company_accounts.forms
import registration.views


urlpatterns = [
    # Examples:
    url(r'^$', TemplateView.as_view(template_name='index.html'), name='home'),
    url(r'^request_info/$', views.RequestInfoView.as_view(template_name='request_info.html'), name='request_info'),
    url(r'^about/$', views.RedirectToIndexView.as_view(), name='about'),
    url(r'^benefits/$', TemplateView.as_view(template_name='benefits.html'), name='benefits'),
    url(r'^pricing/$', TemplateView.as_view(template_name='pricing.html'), name='pricing'),
    url(r'^support/$', views.SupportView.as_view(), name='support'),

    url(r'^admin/', include(admin.site.urls)),
    url(r'^company_accounts/',
        include('company_accounts.urls',
                app_name='company_accounts', namespace='company-accounts')),
    url(r'^billing/', include('billing.urls')),
    url(r'^accounts_receivable/', include('accounts_receivable.urls')),
    url(r'^reports/', include('reports.urls')),

    # Translated login & register forms
#    url(r'^accounts/login/$', 'django.contrib.auth.views.login',
#        {'authentication_form': company_accounts.forms.LoginForm},
#        name='auth_login'),
#    url(r'^accounts/register/$', 
#        registration.views.RegistrationView.as_view(form_class=company_accounts.forms.MyUserCreationForm),
#        name='registration_register'),

    url(r'^accounts/', include('registration.backends.default.urls')),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
