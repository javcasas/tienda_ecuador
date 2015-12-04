from django.conf.urls import patterns, url
from django.views.generic import TemplateView
from public_receipts import views

urlpatterns = patterns(
    '',
    # Index views
    url(r'^$', views.ReceiptForm.as_view(), name='index'),

    url(r'^comprobante/(?P<clave>[0-9]+)/$',
        views.ReceiptView.as_view(), name='receipt_view'),
    url(r'^comprobante/(?P<clave>[0-9]+)/bill/$',  # FIXME: remove
        views.ReceiptView.as_view(template_name='billing/bill_emitted_detail.html'), name='receipt_view_bill'),
)
