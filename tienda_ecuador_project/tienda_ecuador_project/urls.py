from django.conf.urls import include, url
from django.contrib import admin
from django.views.generic import TemplateView
from django.conf.urls.static import static
from django.conf import settings
import views


urlpatterns = [
    # Examples:
    url(r'^$', TemplateView.as_view(template_name='index.html'), name='home'),
    url(r'^form/$', TemplateView.as_view(template_name='request_form.html'), name='form'),  # FIXME:remove
    url(r'^request_info/$', views.RequestInfoView.as_view(template_name='request_info.html'), name='request_info'),
    url(r'^about/$', views.RedirectToIndexView.as_view(), name='about'),
    url(r'^benefits/$', TemplateView.as_view(template_name='benefits.html'), name='benefits'),
    url(r'^support/$', views.SupportView.as_view(), name='support'),

    url(r'^admin/', include(admin.site.urls)),
    url(r'^billing/', include('billing.urls')),
    url(r'^accounts_receivable/', include('accounts_receivable.urls')),
    url(r'^accounts/', include('registration.backends.simple.urls')),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
