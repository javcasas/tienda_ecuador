import tempfile
import os
import base64
import pytz
from datetime import datetime, timedelta
from io import BytesIO

from reportlab.pdfgen import canvas

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
from django.http import HttpResponse

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


class PublicReceiptView(object):
    def get_receipt_data(self, clave_acceso):
        classes = [
            (billing.models.Bill,
                {'template': 'public_receipts/bill_detail.html',
                 'var_name': 'bill',
                 }),
        ]
        for cls, data in classes:
            try:
                ob = cls.objects.get(clave_acceso=clave_acceso)
                res = data.copy()
                res['object'] = ob
                return res
            except cls.DoesNotExist:
                pass
        else:
            return None


class ReceiptView(PublicReceiptView, View):
    """
    """
    template_name = None

    def get(self, request, clave):
        data = self.get_receipt_data(clave)
        if data:
            return render(request,
                          self.template_name or data['template'],
                          {data['var_name']: data['object']})
        else:
            return render(request,
                          'public_receipts/not_found.html',
                          {'clave': clave})

class ReceiptXMLView(PublicReceiptView, View):
    """
    """
    template_name = None

    def get(self, request, clave):
        data = self.get_receipt_data(clave)
        if data:
            ob = data['object']
            response = HttpResponse(ob.xml_content, content_type='text/xml; charset=utf-8')
            response['Content-Disposition'] = 'attachment; filename={}.xml'.format(ob.number)
            return response
        else:
            return render(request,
                          'public_receipts/not_found.html',
                          {'clave': clave})


class ReceiptRIDEView(PublicReceiptView, View):
    """
    """
    template_name = None

    def get(self, request, clave):
        data = self.get_receipt_data(clave)
        if data:
            ob = data['object']
            response = HttpResponse(content_type='application/pdf')
            response['Content-Disposition'] = 'attachment; filename="{}.pdf"'.format(ob.number)
            import gen_ride
            reload(gen_ride)
            pdf = gen_ride.gen_bill_ride(ob)
            response.write(pdf)
            return response
        else:
            return render(request,
                          'public_receipts/not_found.html',
                          {'clave': clave})
