import tempfile
import os
import base64
import pytz
from datetime import datetime, timedelta

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.generic import View
from django.views.generic.list import ListView
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.core.urlresolvers import reverse
from django.http import JsonResponse
from django.forms.models import model_to_dict

from company_accounts.views import CompanyView, CompanySelected

tz = pytz.timezone('America/Guayaquil')


class ReportsIndexView(CompanyView,
                       CompanySelected,
                       DetailView):
    """
    View that shows a general index for a given company
    """
    template_name = 'reports/company_index.html'
