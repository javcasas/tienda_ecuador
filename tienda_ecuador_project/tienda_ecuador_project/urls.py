from django.conf.urls import include, url
from django.contrib import admin
from django.views.generic import TemplateView
from django.conf.urls.static import static
from django.conf import settings
import views
import billing
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
    url(r'^billing/', include('billing.urls')),
    url(r'^accounts_receivable/', include('accounts_receivable.urls')),

    # Translated login & register forms
    url(r'^accounts/login/$', 'django.contrib.auth.views.login',
        {'authentication_form': billing.forms.LoginForm},
        name='auth_login'),
    url(r'^accounts/register/$', 
        registration.views.RegistrationView.as_view(form_class=billing.forms.MyUserCreationForm),
        name='registration_register'),

    url(r'^accounts/', include('registration.backends.simple.urls')),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
