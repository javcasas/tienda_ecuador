from django.conf.urls import patterns, url
from reports import views

urlpatterns = [
    # Index views
    url(r'^(?P<pk>[0-9]+)$',
        views.ReportsIndexView.as_view(), name='reports_index'),

    url(r'^sri/(?P<company_id>[0-9]+)/$',
        views.PaymentDateListReport.as_view(),
        name='report_sri_index'),

    # SRI Income
    url(r'^sri/(?P<company_id>[0-9]+)/income/(?P<year>[0-9]+)/(?P<month>[0-9]+)/(?P<day>[0-9]+)/$',
        views.PaymentDayListReport.as_view(),
        name='report_daily_income'),
    url(r'^sri/(?P<company_id>[0-9]+)/income/(?P<year>[0-9]+)/(?P<month>[0-9]+)/(?P<day>[0-9]+)/pruebas/$',
        views.PaymentDayListReport.as_view(ambiente_sri='pruebas'),
        name='report_daily_income.pruebas'),

    url(r'^sri/(?P<company_id>[0-9]+)/income/(?P<year>[0-9]+)/(?P<month>[0-9]+)/$',
        views.PaymentMonthListReport.as_view(),
        name='report_monthly_income'),
    url(r'^sri/(?P<company_id>[0-9]+)/income/(?P<year>[0-9]+)/(?P<month>[0-9]+)/pruebas/$',
        views.PaymentMonthListReport.as_view(ambiente_sri='pruebas'),
        name='report_monthly_income.pruebas'),

    url(r'^sri/(?P<company_id>[0-9]+)/income/(?P<year>[0-9]+)/$',
        views.PaymentYearListReport.as_view(),
        name='report_yearly_income'),
    url(r'^sri/(?P<company_id>[0-9]+)/income/(?P<year>[0-9]+)/$',
        views.PaymentYearListReport.as_view(ambiente_sri='pruebas'),
        name='report_yearly_income.pruebas'),

    # SRI Bills
    url(r'^sri/(?P<company_id>[0-9]+)/bills/(?P<year>[0-9]+)/(?P<month>[0-9]+)/(?P<day>[0-9]+)/$',
        views.BillDayListReport.as_view(),
        name='report_daily_bills'),
    url(r'^sri/(?P<company_id>[0-9]+)/bills/(?P<year>[0-9]+)/(?P<month>[0-9]+)/(?P<day>[0-9]+)/pruebas/$',
        views.BillDayListReport.as_view(ambiente_sri='pruebas'),
        name='report_daily_bills.pruebas'),

    url(r'^sri/(?P<company_id>[0-9]+)/bills/(?P<year>[0-9]+)/(?P<month>[0-9]+)/$',
        views.BillMonthListReport.as_view(),
        name='report_monthly_bills'),
    url(r'^sri/(?P<company_id>[0-9]+)/bills/(?P<year>[0-9]+)/(?P<month>[0-9]+)/pruebas/$',
        views.BillMonthListReport.as_view(ambiente_sri='pruebas'),
        name='report_monthly_bills.pruebas'),

    url(r'^sri/(?P<company_id>[0-9]+)/bills/(?P<year>[0-9]+)/$',
        views.BillYearListReport.as_view(),
        name='report_yearly_bills'),
    url(r'^sri/(?P<company_id>[0-9]+)/bills/(?P<year>[0-9]+)/pruebas/$',
        views.BillYearListReport.as_view(ambiente_sri='pruebas'),
        name='report_yearly_bills.pruebas'),
]
