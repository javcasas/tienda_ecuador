from django.conf.urls import patterns, url
from purchases import views, forms
from django.contrib.auth.decorators import login_required

urlpatterns = patterns(
    '',
    # Index views
    #url(r'^$',
    #    login_required(views.LoggedInIndexView.as_view()), name='company_select'),

)
