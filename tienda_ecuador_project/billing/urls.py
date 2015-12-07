from django.conf.urls import patterns, url
from billing import views
from util.sri_models import SRIStatus, AmbienteSRI

urlpatterns = patterns(
    '',
    #######################
    # Index views
    #######################
    url(r'^$', views.index, name='billing_index'),
    url(r'^(?P<company_id>[0-9]+)/$',
        views.CompanyIndex.as_view(), name='company_index'),

    #######################
    # Item views
    #######################
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

    #######################
    # Customer views
    #######################
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
    # Bill views          #
    #######################

    # Bill lists by status
    url(r'^bill/list/c/(?P<company_id>[0-9]+)/$',
        views.BillCompanyListView.as_view(
            queryset_filters={'status': SRIStatus.options.NotSent}
        ), name='bill_company_index'),
    url(r'^bill/list/c/(?P<company_id>[0-9]+)/ready_to_send/$',
        views.BillCompanyListView.as_view(
            queryset_filters={'status': SRIStatus.options.ReadyToSend}
        ), name='bill_company_index.ready_to_send'),
    url(r'^bill/list/c/(?P<company_id>[0-9]+)/sent/$',
        views.BillCompanyListView.as_view(
            queryset_filters={'status': SRIStatus.options.Sent}
        ), name='bill_company_index.sent'),
    url(r'^bill/list/c/(?P<company_id>[0-9]+)/accepted/$',
        views.BillCompanyListView.as_view(
            queryset_filters={'status': SRIStatus.options.Accepted}
        ), name='bill_company_index.accepted'),
    url(r'^bill/list/c/(?P<company_id>[0-9]+)/annulled/$',
        views.BillCompanyListView.as_view(
            queryset_filters={'status': SRIStatus.options.Annulled}
        ), name='bill_company_index.annulled'),

    url(r'^bill/list/e/(?P<establecimiento_id>[0-9]+)/$',
        views.BillEstablecimientoListView.as_view(), name='bill_establecimiento_index'),
    url(r'^bill/list/pe/(?P<punto_emision_id>[0-9]+)/$',
        views.BillPuntoEmisionListView.as_view(), name='bill_punto_emision_index'),
    # Solo se pueden hacer facturas en un punto de emision
    url(r'^proforma_bill/new/(?P<punto_emision_id>[0-9]+)/$',
        views.BillCreateView.as_view(), name='bill_create'),
    url(r'^proforma_bill/(?P<pk>[0-9]+)/read/$',
        views.BillDetailView.as_view(), name='bill_detail'),
    url(r'^proforma_bill/(?P<pk>[0-9]+)/update/$',
        views.BillUpdateView.as_view(), name='bill_update'),
    url(r'^proforma_bill/(?P<bill_id>[0-9]+)/new_customer/$',
        views.BillNewCustomerView.as_view(), name='bill_new_customer'),
    url(r'^proforma_bill/(?P<pk>[0-9]+)/delete/$',
        views.BillDeleteView.as_view(), name='bill_delete'),

    url(r'^proforma_bill/(?P<pk>[0-9]+)/item_table/$',
        views.BillDetailView.as_view(
            template_name_suffix='_detail_item_table'),
        name='bill_detail_item_table'),

    url(r'^proforma_bill/(?P<pk>[0-9]+)/totals_table/$',
        views.BillDetailView.as_view(
            template_name_suffix='_detail_totals_table'),
        name='bill_detail_totals_table'),

    url(r'^proforma_bill/(?P<pk>[0-9]+)/payment_table/$',
        views.BillDetailView.as_view(
            template_name_suffix='_detail_payment_table'),
        name='bill_detail_payment_table'),

    #######################
    # Bill emitting views
    #######################
    url(r'^bill/(?P<pk>[0-9]+)/emit/accept/$',
        views.BillEmitAcceptView.as_view(),
        name='bill_emit_accept'),
    url(r'^bill/(?P<pk>[0-9]+)/emit/gen_xml/$',
        views.BillEmitGenXMLView.as_view(),
        name='bill_emit_gen_xml'),
    url(r'^bill/(?P<pk>[0-9]+)/emit/send_to_sri/$',
        views.BillEmitSendToSRIView.as_view(),
        name='bill_emit_send_to_sri'),
    url(r'^bill/(?P<pk>[0-9]+)/emit/validate/$',
        views.BillEmitValidateView.as_view(),
        name='bill_emit_validate'),
    url(r'^bill/(?P<pk>[0-9]+)/emit/check_annulled/$',
        views.BillEmitCheckAnnulledView.as_view(),
        name='bill_emit_check_annulled'),

    url(r'^bill/emit/general_progress/$',
        views.BillEmitGeneralProgressView.as_view(), name='bill_emit_progress'),

    # Proforma bill item views
    url(r'^proforma_bill/(?P<bill_id>[0-9]+)/add_item/$',
        views.BillAddItemView.as_view(),
        name='bill_add_item'),
    url(r'^proforma_bill/item/(?P<pk>[0-9]+)/edit/$',
        views.BillItemUpdateView.as_view(),
        name='billitem_update'),
    url(r'^proforma_bill/item/(?P<pk>[0-9]+)/delete/$',
        views.BillItemDeleteView.as_view(),
        name='billitem_delete'),

    url(r'^proforma_bill/item/(?P<pk>[0-9]+)/update_js/$',
        views.BillItemUpdateViewJS.as_view(),
        name='billitem_update_js'),

    # orma bill payment views
    url(r'^proforma_bill/(?P<pk>[0-9]+)/payment/$',
        views.BillPaymentView.as_view(),
        name='bill_payment_details'),

    # Emitted bill Views
    url(r'^emitted_bill/(?P<pk>[0-9]+)/read/$',
        views.BillDetailView.as_view(
            template_name_suffix='_emitted',
        ), name='emitted_bill_detail'),
    url(r'^bill_list/(?P<company_id>[0-9]+)/$',
        views.BillListView.as_view(
            template_name='billing/bill/bill_list_table.html',
        ), name='bill_list_table'),
)
