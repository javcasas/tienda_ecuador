import pytz
from email.mime.text import MIMEText
from subprocess import Popen, PIPE

from django.shortcuts import render, redirect
from django.views.generic import View

tz = pytz.timezone('America/Guayaquil')


class RequestInfoView(View):
    template_name = 'request_info.html'

    def get(self, request):
        return redirect("home")

    def post(self, request):
        msg = MIMEText('Interesado en DSSTI Facturas\nEmpresa: {}\nEmail: {}\n'.format(
            request.POST['company'],
            request.POST['email']))
        msg["From"] = "ventas@dssti.com"
        msg["To"] = "ventas@dssti.com"
        msg["Subject"] = "Interesado en DSSTI Facturas"
        p = Popen(["/usr/bin/sendmail", "-t", "-oi"], stdin=PIPE)
        p.communicate(msg.as_string())
        return render(request, self.template_name, {})


class RedirectToIndexView(View):
    def get(self, request):
        return redirect("home")


class SupportView(View):
    def get(self, request):
        return render(request, 'support.html')

    def post(self, request):
        name = request.POST['name']
        company = request.POST['company']
        email = request.POST['email']
        query_text = request.POST['query-text']
        msg_text = u'''
Peticion de Soporte
Nombre: {name}
Empresa: {company}
Email: {email}

{query_text}
'''
        msg = MIMEText(msg_text.format(name=name, company=company,
                                       email=email, query_text=query_text))
        msg["From"] = "soporte@dssti.com"
        msg["To"] = "soporte@dssti.com"
        msg["Subject"] = "Peticion de Soporte"
        p = Popen(["/usr/bin/sendmail", "-t", "-oi"], stdin=PIPE)
        p.communicate(msg.as_string())
        return render(request, 'support_submitted.html', {})
