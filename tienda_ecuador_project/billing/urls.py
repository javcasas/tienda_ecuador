from django.conf.urls import patterns, url
from billing import views

urlpatterns = patterns('',
    url(r'^$', views.index, name='index'),
    url(r'^(?P<company_id>[0-9]+)/$', views.company_index, name='company_index'),
    url(r'^(?P<company_id>[0-9]+)/item/(?P<item_id>[0-9]+)/$', views.view_item, name='view_item'),
    url(r'^(?P<company_id>[0-9]+)/item/(?P<item_id>[0-9]+)/edit/$', views.EditItem.as_view(), name='edit_item'),
#
    url(r'^(?P<company_id>[0-9]+)/bill/new/$', views.NewBill.as_view(), name='new_bill'),
    url(r'^(?P<company_id>[0-9]+)/bill/(?P<bill_id>[0-9]+)/$', views.view_bill, name='view_bill'),
    url(r'^(?P<company_id>[0-9]+)/bill/(?P<bill_id>[0-9]+)/edit/$', views.edit_bill, name='edit_bill'),
#    url(r'^bill/(?P<bill_id>[0-9]+)/delete/$', views.delete_bill, name='delete_bill'),
#
#    url(r'^bill/(?P<bill_id>[0-9]+)/add_item/$', views.add_item_to_bill, name='add_item_to_bill'),
#    url(r'^bill/(?P<bill_id>[0-9]+)/item/(?P<item_id>[0-9]+)/edit/$', views.edit_item_in_bill, name='edit_item_in_bill'),
#    url(r'^bill/(?P<bill_id>[0-9]+)/item/(?P<item_id>[0-9]+)/delete/$', views.delete_item_in_bill, name='delete_item_from_bill'),
)
