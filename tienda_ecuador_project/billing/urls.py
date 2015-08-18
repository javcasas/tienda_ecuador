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
    url(r'^item/index/(?P<company_id>[0-9]+)/$',
        views.ItemListView.as_view(), name='item_index'),
    url(r'^item/index/(?P<company_id>[0-9]+)/json/$',
        views.ItemListViewJson.as_view(), name='item_index_json'),
    url(r'^item/new/c/(?P<company_id>[0-9]+)/$',
        views.ItemCreateView.as_view(), name='item_create'),
    url(r'^item/detail/(?P<pk>[0-9]+)/$',
        views.ItemDetailView.as_view(), name='item_detail'),
    url(r'^item/edit/(?P<pk>[0-9]+)/$',
        views.ItemUpdateView.as_view(), name='item_update'),
    url(r'^item/delete/(?P<pk>[0-9]+)/$',
        views.ItemDeleteView.as_view(), name='item_delete'),

    # Customer views
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

    #######################
    # Proforma bill views #
    #######################
    url(r'^proforma_bill/list/c/(?P<company_id>[0-9]+)/$',
        views.ProformaBillCompanyListView.as_view(), name='proformabill_company_index'),
    url(r'^proforma_bill/list/e/(?P<establecimiento_id>[0-9]+)/$',
        views.ProformaBillEstablecimientoListView.as_view(), name='proformabill_establecimiento_index'),
    url(r'^proforma_bill/list/pe/(?P<punto_emision_id>[0-9]+)/$',
        views.ProformaBillPuntoEmisionListView.as_view(), name='proformabill_punto_emision_index'),
    # Solo se pueden hacer facturas en un punto de emision
    url(r'^proforma_bill/new/(?P<punto_emision_id>[0-9]+)/$',
        views.ProformaBillCreateView.as_view(), name='proformabill_create'),
    url(r'^proforma_bill/(?P<pk>[0-9]+)/read/$',
        views.ProformaBillDetailView.as_view(), name='proformabill_detail'),
    url(r'^proforma_bill/(?P<pk>[0-9]+)/update/$',
        views.ProformaBillUpdateView.as_view(), name='proformabill_update'),
    url(r'^proforma_bill/(?P<pk>[0-9]+)/delete/$',
        views.ProformaBillDeleteView.as_view(), name='proformabill_delete'),

    # Proforma bill emitting views
    url(r'^proforma_bill/(?P<pk>[0-9]+)/emit/$',
        views.ProformaBillEmitView.as_view(),
        name='proformabill_emit_to_bill'),
    url(r'^proforma_bill/(?P<pk>[0-9]+)/emit/gen_xml/$',
        views.ProformaBillEmitGenXMLView.as_view(),
        name='proformabill_emit_gen_xml'),

    # Proforma bill item views
    url(r'^proforma_bill/(?P<proformabill_id>[0-9]+)/add_item/$',
        views.ProformaBillAddItemView.as_view(),
        name='proformabill_add_item'),
    url(r'^proforma_bill/item/(?P<pk>[0-9]+)/edit/$',
        views.ProformaBillItemUpdateView.as_view(),
        name='proformabillitem_update'),
    url(r'^proforma_bill/item/(?P<pk>[0-9]+)/delete/$',
        views.ProformaBillItemDeleteView.as_view(),
        name='proformabillitem_delete'),

    # Report views
    url(r'^report/(?P<company_id>[0-9]+)/bills/day/(?P<year>[0-9]+)/(?P<month>[0-9]+)/(?P<day>[0-9]+)/$',
        views.BillDayListReport.as_view(),
        name='report_daily_bills'),
)
