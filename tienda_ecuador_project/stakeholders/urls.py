from django.conf.urls import patterns, url
from stakeholders import views

urlpatterns = [
    url(r'^customer/list/(?P<company_id>[0-9]+)/$',
        views.CustomerListView.as_view(), name='customer_index'),
    url(r'^customer/new/(?P<company_id>[0-9]+)/$',
        views.CustomerCreateView.as_view(), name='customer_create'),
    url(r'^customer/read/(?P<pk>[0-9]+)/$',
        views.CustomerDetailView.as_view(), name='customer_detail'),
    url(r'^customer/update/(?P<pk>[0-9]+)/$',
        views.CustomerUpdateView.as_view(), name='customer_update'),
    url(r'^customer/delete/(?P<pk>[0-9]+)/$',
        views.CustomerDeleteView.as_view(), name='customer_delete'),
]
