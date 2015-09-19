from django.conf.urls import include, url
from django.contrib import admin
from django.views.generic import TemplateView
from django.conf.urls.static import static
from django.conf import settings

urlpatterns = [
    # Examples:
    url(r'^$', TemplateView.as_view(template_name='index.html'), name='home'),
    url(r'^form/$', TemplateView.as_view(template_name='request_form.html'), name='form'),  # FIXME:remove
    url(r'^request_info/$', TemplateView.as_view(template_name='request_info.html'), name='request_info'),
    url(r'^about/$', TemplateView.as_view(template_name='request_form.html'), name='about'),  # FIXME: use proper template
    url(r'^benefits/$', TemplateView.as_view(template_name='benefits.html'), name='benefits'),
    url(r'^support/$', TemplateView.as_view(template_name='request_form.html'), name='support'),  # FIXME: use proper template

    url(r'^admin/', include(admin.site.urls)),
    url(r'^billing/', include('billing.urls')),
    url(r'^accounts_receivable/', include('accounts_receivable.urls')),
    url(r'^accounts/', include('registration.backends.simple.urls')),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
