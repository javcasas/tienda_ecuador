from django.conf.urls import patterns, url
from accounts_receivable import views

urlpatterns = patterns(
    '',
    # Index views
    url(r'^(?P<pk>[0-9]+)$',
        views.CompanyIndexView.as_view(), name='accounts_receivable_index'),

    # Receivable views
    url(r'^receivable/(?P<pk>[0-9]+)$',
        views.ReceivableDetailView.as_view(), name='receivable_detail'),
    url(r'^receivable/(?P<pk>[0-9]+)/edit/$',
        views.ReceivableUpdateView.as_view(), name='receivable_update'),
    url(r'^receivable/(?P<pk>[0-9]+)/confirm_received/$',
        views.ReceivableConfirmReceivedView.as_view(), name='receivable_confirm_received'),
    url(r'^receivable/(?P<receivable_id>[0-9]+)/claim/$',
        views.PaymentCreateView.as_view(), name='receivable_claim'),
)
