from django.conf.urls import patterns, url
from purchases import views, forms
from django.contrib.auth.decorators import login_required

urlpatterns = patterns(
    '',
    # Index views
    #url(r'^$',
    #    login_required(views.LoggedInIndexView.as_view()), name='company_select'),
    url(r'^(?P<pk>[0-9]+)/$',
        views.PurchasesMainMenuView.as_view(), name='purchases_main_menu'),

    # Purchase views
    url(r'^create_from_xml/(?P<company_id>[0-9]+)/$',
        views.PurchaseCreateFromXMLView.as_view(), name='purchase_create_from_xml'),
    url(r'^list/(?P<company_id>[0-9]+)/$',
        views.PurchaseListView.as_view(), name='purchase_list'),
    url(r'^purchase/(?P<pk>[0-9]+)/$',
        views.PurchaseDetailView.as_view(), name='purchase_detail'),
    url(r'^generate_retention/(?P<pk>[0-9]+)/$',
        views.PurchaseGenerateRetentionView.as_view(), name='purchase_generate_retention'),
    url(r'^add_items_to_inventory/(?P<pk>[0-9]+)/$',
        views.PurchaseAddItemsToInventoryView.as_view(), name='purchase_add_items_to_inventory_xml'),
    url(r'^finish/(?P<pk>[0-9]+)/$',
        views.PurchaseFinishView.as_view(), name='purchase_finish'),
    url(r'^archive/(?P<company_id>[0-9]+)/(?P<year>[0-9]{4})/$',
        views.PurchaseYearView.as_view(
            #template_name='purchases/purchase_list_table.html',
        ),
        name="purchase_year_archive"),
    url(r'^archive/(?P<company_id>[0-9]+)/(?P<year>[0-9]{4})/(?P<month>[0-9]+)/$',
        views.PurchaseMonthView.as_view(
            month_format="%m",
        ),
        name="purchase_month_archive"),
    url(r'^archive/(?P<company_id>[0-9]+)/(?P<year>[0-9]{4})/(?P<month>[0-9]+)/(?P<day>[0-9]+)/$',
        views.PurchaseDayView.as_view(
            month_format="%m",
        ),
        name="purchase_day_archive"),
)
