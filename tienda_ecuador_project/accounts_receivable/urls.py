from django.conf.urls import patterns, url
from accounts_receivable import views

urlpatterns = patterns(
    '',
    # Index views
    url(r'^(?P<pk>[0-9]+)$',
        views.CompanyIndexView.as_view(), name='accounts_receivable_index'),
)
