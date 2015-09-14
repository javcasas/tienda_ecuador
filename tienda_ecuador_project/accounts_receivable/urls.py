from django.conf.urls import patterns, url
from accounts_receivable import views

urlpatterns = patterns(
    '',
    # Index views
    url(r'^$',
        views.index, name='index'),
)
