from django.conf.urls import patterns, url
from reports import views

urlpatterns = patterns(
    '',
    # Index views
    url(r'^(?P<pk>[0-9]+)$',
        views.ReportsIndexView.as_view(), name='reports_index'),
)
