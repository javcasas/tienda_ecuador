from django.conf.urls import patterns, url
from inventory import views

urlpatterns = patterns(
    '',
    # Main menu
    url(r'^(?P<pk>[0-9]+)/$',
        views.CompanyProfileView.as_view(
            template_name='inventory/inventory_main_menu.html',
        ), name='inventory_main_menu'),
    # Item views
    url(r'^item/index/(?P<company_id>[0-9]+)/$',
        views.ItemListView.as_view(), name='item_index'),
#    url(r'^item/index/(?P<company_id>[0-9]+)/json/$',
#        views.ItemListViewJson.as_view(), name='item_index_json'),
    url(r'^item/new/c/(?P<company_id>[0-9]+)/$',
        views.ItemCreateView.as_view(), name='item_create'),
    url(r'^item/detail/(?P<pk>[0-9]+)/$',
        views.ItemDetailView.as_view(), name='item_detail'),
    url(r'^item/edit/(?P<pk>[0-9]+)/$',
        views.ItemUpdateView.as_view(), name='item_update'),
    url(r'^item/delete/(?P<pk>[0-9]+)/$',
        views.ItemDeleteView.as_view(), name='item_delete'),

    # Batch views
    url(r'^batch/index/(?P<item_id>[0-9]+)/$',
        views.BatchListView.as_view(), name='batch_index'),
    url(r'^batch/new/c/(?P<item_id>[0-9]+)/$',
        views.BatchCreateView.as_view(), name='batch_create'),
    url(r'^batch/detail/(?P<pk>[0-9]+)/$',
        views.BatchDetailView.as_view(), name='batch_detail'),
    url(r'^batch/edit/(?P<pk>[0-9]+)/$',
        views.BatchUpdateView.as_view(), name='batch_update'),
    url(r'^batch/delete/(?P<pk>[0-9]+)/$',
        views.BatchDeleteView.as_view(), name='batch_delete'),

    # SKU views
    url(r'^sku/index/(?P<establecimiento_id>[0-9]+)/$',
        views.SKUEstablecimientoListView.as_view(), name='sku_establecimiento_index'),
    url(r'^sku/new/c/(?P<batch_id>[0-9]+)/$',
        views.SKUCreateView.as_view(), name='sku_create'),
    url(r'^sku/detail/(?P<pk>[0-9]+)/$',
        views.SKUDetailView.as_view(), name='sku_detail'),
    url(r'^sku/edit/(?P<pk>[0-9]+)/$',
        views.SKUUpdateView.as_view(), name='sku_update'),
    url(r'^sku/delete/(?P<pk>[0-9]+)/$',
        views.SKUDeleteView.as_view(), name='sku_delete'),
)
