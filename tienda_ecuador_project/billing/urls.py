from django.conf.urls import patterns, url
from billing import views

urlpatterns = patterns('',
    url(r'^$', views.index, name='index'),
    url(r'^(?P<company_id>[0-9]+)/$', views.CompanyIndex.as_view(), name='company_index'),
    url(r'^(?P<company_id>[0-9]+)/item/$', views.ItemView.as_view(), name='item_index'),
    url(r'^(?P<company_id>[0-9]+)/item/(?P<item_id>[0-9]+)/$', views.ItemView.as_view(), name='item_view'),
    url(r'^(?P<company_id>[0-9]+)/item/(?P<item_id>[0-9]+)/edit/$', views.ItemView.as_view(), name='item_edit'),

#    url(r'^(?P<company_id>[0-9]+)/bill/new/$', views.NewBill.as_view(), name='new_bill'),
#    url(r'^(?P<company_id>[0-9]+)/bill/(?P<bill_id>[0-9]+)/$', views.ViewBill.as_view(), name='view_bill'),
#    url(r'^(?P<company_id>[0-9]+)/bill/(?P<bill_id>[0-9]+)/edit/$', views.EditBill.as_view(), name='edit_bill'),
#    url(r'^(?P<company_id>[0-9]+)/bill/(?P<bill_id>[0-9]+)/delete/$', views.DeleteBill.as_view(), name='delete_bill'),
#
#    url(r'^(?P<company_id>[0-9]+)/bill/(?P<bill_id>[0-9]+)/add_item/$', views.AddItemToBill.as_view(), name='add_item_to_bill'),
#    url(r'^(?P<company_id>[0-9]+)/bill/(?P<bill_id>[0-9]+)/item/(?P<item_id>[0-9]+)/edit/$', views.EditItemInBill.as_view(), name='edit_item_in_bill'),
#    url(r'^(?P<company_id>[0-9]+)/bill/(?P<bill_id>[0-9]+)/item/(?P<item_id>[0-9]+)/delete/$', views.DeleteItemFromBill.as_view(), name='delete_item_from_bill'),
#
#    url(r'^(?P<company_id>[0-9]+)/customer/new/$', views.NewCustomer.as_view(), name='new_customer'),
)
