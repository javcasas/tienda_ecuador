from django.conf.urls import patterns, url
from reports import views

urlpatterns = patterns(
    '',
    # Index views
    url(r'^(?P<pk>[0-9]+)$',
        views.ReportsIndexView.as_view(), name='reports_index'),

    # SRI Income
    url(r'^sri/(?P<company_id>[0-9]+)/income/(?P<year>[0-9]+)/(?P<month>[0-9]+)/(?P<day>[0-9]+)/$',
        views.PaymentDateListReport.as_view(),
        name='report_daily_income'),
    url(r'^sri/(?P<company_id>[0-9]+)/income/(?P<year>[0-9]+)/(?P<month>[0-9]+)/$',
        views.PaymentDateListReport.as_view(),
        name='report_monthly_income'),
    url(r'^sri/(?P<company_id>[0-9]+)/income/(?P<year>[0-9]+)/$',
        views.PaymentDateListReport.as_view(),
        name='report_yearly_income'),
    # SRI Bills
    url(r'^sri/(?P<company_id>[0-9]+)/bills/(?P<year>[0-9]+)/(?P<month>[0-9]+)/(?P<day>[0-9]+)/$',
        views.PaymentDateListReport.as_view(),
        name='report_daily_bills'),
    url(r'^sri/(?P<company_id>[0-9]+)/bills/(?P<year>[0-9]+)/(?P<month>[0-9]+)/$',
        views.PaymentDateListReport.as_view(),
        name='report_monthly_bills'),
    url(r'^sri/(?P<company_id>[0-9]+)/bills/(?P<year>[0-9]+)/$',
        views.PaymentDateListReport.as_view(),
        name='report_yearly_bills'),
)
