from django.conf.urls import patterns, url
from billing import views

urlpatterns = patterns(
    '',
    # Index views
    url(r'^$',
        views.index, name='index'),
    url(r'^(?P<company_id>[0-9]+)/$',
        views.CompanyIndex.as_view(), name='company_index'),

    # Item views
    url(r'^(?P<company_id>[0-9]+)/item/$',
        views.ItemListView.as_view(), name='item_index'),
    url(r'^(?P<company_id>[0-9]+)/item/json/$',
        views.ItemListViewJson.as_view(), name='item_index_json'),
    url(r'^(?P<company_id>[0-9]+)/item/new/$',
        views.ItemCreateView.as_view(), name='item_create'),
    url(r'^(?P<company_id>[0-9]+)/item/(?P<pk>[0-9]+)/$',
        views.ItemDetailView.as_view(), name='item_detail'),
    url(r'^(?P<company_id>[0-9]+)/item/(?P<pk>[0-9]+)/edit/$',
        views.ItemUpdateView.as_view(), name='item_update'),
    url(r'^(?P<company_id>[0-9]+)/item/(?P<pk>[0-9]+)/delete/$',
        views.ItemDeleteView.as_view(), name='item_delete'),

    # Customer views
    url(r'^(?P<company_id>[0-9]+)/customer/$',
        views.CustomerListView.as_view(), name='customer_index'),
    url(r'^(?P<company_id>[0-9]+)/customer/new/$',
        views.CustomerCreateView.as_view(), name='customer_create'),
    url(r'^(?P<company_id>[0-9]+)/customer/(?P<pk>[0-9]+)/$',
        views.CustomerDetailView.as_view(), name='customer_detail'),
    url(r'^(?P<company_id>[0-9]+)/customer/(?P<pk>[0-9]+)/edit/$',
        views.CustomerUpdateView.as_view(), name='customer_update'),
    url(r'^(?P<company_id>[0-9]+)/customer/(?P<pk>[0-9]+)/delete/$',
        views.CustomerDeleteView.as_view(), name='customer_delete'),

    #######################
    # Proforma bill views #
    #######################
    url(r'^proforma_bill/c/(?P<company_id>[0-9]+)/$',
        views.ProformaBillCompanyListView.as_view(), name='proformabill_company_index'),
    url(r'^(?P<establecimiento_id>[0-9]+)/e/proforma_bill/$',
        views.ProformaBillEstablecimientoListView.as_view(), name='proformabill_establecimiento_index'),
    url(r'^(?P<punto_emision_id>[0-9]+)/p/proforma_bill/$',
        views.ProformaBillPuntoEmisionListView.as_view(), name='proformabill_punto_emision_index'),
    # Solo se pueden hacer facturas en un punto de emision
    url(r'^proforma_bill/p/(?P<punto_emision_id>[0-9]+)/$',
        views.ProformaBillCreateView.as_view(), name='proformabill_create'),
    url(r'^proforma_bill/(?P<company_id>[0-9]+)/proforma_bill/(?P<pk>[0-9]+)/$',
        views.ProformaBillDetailView.as_view(), name='proformabill_detail'),
    url(r'^proforma_bill/(?P<company_id>[0-9]+)/proforma_bill/(?P<pk>[0-9]+)/edit/$',
        views.ProformaBillUpdateView.as_view(), name='proformabill_update'),
    url(r'^proforma_bill/(?P<company_id>[0-9]+)/proforma_bill/(?P<pk>[0-9]+)/delete/$',
        views.ProformaBillDeleteView.as_view(), name='proformabill_delete'),

    # Proforma bill emitting views
    url(r'^(?P<company_id>[0-9]+)/proforma_bill/(?P<pk>[0-9]+)/emit/$',
        views.ProformaBillEmitView.as_view(),
        name='proformabill_emit_to_bill'),
    url(r'^(?P<company_id>[0-9]+)/proforma_bill/(?P<pk>[0-9]+)/emit/gen_xml/$',
        views.ProformaBillEmitGenXMLView.as_view(),
        name='proformabill_emit_gen_xml'),

    # Proforma bill item views
    url(r'^(?P<company_id>[0-9]+)/proforma_bill/(?P<proformabill_id>[0-9]+)/add_item/$',
        views.ProformaBillAddItemView.as_view(),
        name='proformabill_add_item'),
    url(r'^(?P<company_id>[0-9]+)/proforma_bill/(?P<proformabill_id>[0-9]+)/(?P<pk>[0-9]+)/edit/$',
        views.ProformaBillItemUpdateView.as_view(),
        name='proformabillitem_update'),
    url(r'^(?P<company_id>[0-9]+)/proforma_bill/(?P<proformabill_id>[0-9]+)/(?P<pk>[0-9]+)/delete/$',
        views.ProformaBillItemDeleteView.as_view(),
        name='proformabillitem_delete'),
)
