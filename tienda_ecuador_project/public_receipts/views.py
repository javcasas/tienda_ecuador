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
from django.views.generic import TemplateView

import billing.models
from company_accounts.views import CompanyView, CompanySelected

tz = pytz.timezone('America/Guayaquil')

class ReceiptForm(TemplateView):
    template_name='public_receipts/index.html'

    def post(self, request):
        if request.POST['clave']:
            return redirect('public-receipts:receipt_view', request.POST['clave'])
        else:
            return self.get(request)
        

class ReceiptView(View):
    """
    """
    template_name = None
    def get(self, request, clave):
        classes = [
            (billing.models.Bill,
             {'template': 'public_receipts/bill_detail.html',
              'var_name': 'bill',
             }
            ),
    ]
        for cls, data in classes:
            try:
                ob = cls.objects.get(clave_acceso=clave)
                return render(request,
                              self.template_name or data['template'],
                              {data['var_name']: ob})
            except cls.DoesNotExist:
                pass
        else:
            return render(request,
                          'public_receipts/not_found.html',
                          {'clave': clave})
