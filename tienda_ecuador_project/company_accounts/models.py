# * encoding: utf-8 *
from datetime import date, timedelta, datetime
import json
import pytz

from django.db import models
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.core.files.storage import FileSystemStorage

from util import signature


ambiente_sri_OPTIONS = (
    ('pruebas', 'Pruebas'),
    ('produccion', 'Producción')
)

Company_licencia_OPTIONS = (
    ('demo', 'Demo'),
    ('basic', 'Basic'),
    ('professional', 'Professional'),
    ('enterprise', 'Enterprise'),
)


class Licence(models.Model):
    """
    A licence model
    """
    licence = models.CharField(
        max_length=20,
        choices=Company_licencia_OPTIONS,
        default="demo")
    expiration = models.DateField(
        default=date(2010, 1, 1))
    next_licence = models.CharField(
        max_length=20,
        choices=Company_licencia_OPTIONS,
        default="demo")

    @property
    def company(self):
        return Company.objects.get(licence=self)

    @property
    def expired(self):
        return date.today() > self.expiration + timedelta(days=3)

    @property
    def effective_licence(self):
        if self.expired:
            return "demo"
        else:
            return self.licence

    @property
    def days_to_expiration(self):
        if not self.expired:
            return (self.expiration - date.today()).days
        else:
            return 0

    def approve(self, new_date):
        """
        Approve the next licence with the new expiration date
        """
        assert self.next_licence != 'demo'
        next_licence = self.next_licence
        LicenceHistory(
            licence=self,
            date=datetime.now(tz=pytz.timezone('America/Guayaquil')),
            action=json.dumps(
                {"action": "approve",
                 "next_licence": str(next_licence),
                 "old_date": str(self.expiration),
                 "new_date": str(new_date),
                 'user_viewable': True,
                 }
            )).save()
        self.licence = next_licence
        self.expiration = new_date
        self.save()

    def get_history(self):
        return LicenceHistory.objects.filter(licence=self)

    def __unicode__(self):
        return dict(Company_licencia_OPTIONS)[self.licence]


def default_licence():
    n = Licence()
    n.save()
    LicenceHistory(
        licence=n,
        date=datetime.now(tz=pytz.timezone('America/Guayaquil')),
        action=json.dumps(
            {"action": "create",
             'user_viewable': True,
             "reason": "New company created"}
        )).save()
    return n.id


class OverwritingStorage(FileSystemStorage):
    def save(self, path, *args, **kwargs):
        if self.exists(path):
            self.delete(path)
        return super(OverwritingStorage, self).save(path, *args, **kwargs)


class Issue(object):
    def __init__(self, level, message, url, button_text='Arreglar'):
        self.message = message
        self.level = level
        self.url = url
        self.button_text = button_text

    def __unicode__(self):
        return u"{} - {}".format(self.level, self.message)

    def __repr__(self):
        return "<issue {}>".format(
            self.__unicode__().encode("ascii", "replace"))


def logo_path_generator(instance, filename):
    ext = filename.split(".")[-1]
    return 'static/company_logos/{id}_{ruc}.{ext}'.format(
        id=instance.id, ruc=instance.ruc, ext=ext)


class Company(models.Model):
    """
    Represents a company
    """
    nombre_comercial = models.CharField(max_length=100)
    ruc = models.CharField(max_length=100)
    razon_social = models.CharField(max_length=100)
    direccion_matriz = models.CharField(max_length=100)
    contribuyente_especial = models.CharField(max_length=20, blank=True)
    obligado_contabilidad = models.BooleanField(default=False)
    licence = models.ForeignKey(Licence, default=default_licence)
    siguiente_numero_proforma = models.IntegerField(default=1)
    logo = models.ImageField(
        upload_to=logo_path_generator,
        blank=True,
        storage=OverwritingStorage())
    cert = models.CharField(max_length=20000, blank=True)
    key = models.CharField(max_length=100, blank=True)

    def __unicode__(self):
        return self.razon_social

    def get_absolute_url(self):
        return reverse("company_accounts:company_profile",
                       kwargs={'pk': self.pk})

    @property
    def can_sign(self):
        try:
            return signature.has_cert(self.ruc, self.id)
        except signature.Timeout:
            return False

    @property
    def establecimientos(self):
        return Establecimiento.objects.filter(company=self)

    def get_logo(self):
        return self.logo
        if self.licence.licence in ['demo', 'professional', 'enterprise']:
            return self.logo

    @property
    def issues(self):
        """
        Makes a list of issues in a given company to be shown
        """
        res = []
        if self.licence.licence == 'demo' and self.licence.next_licence == 'demo':
            res.append(
                Issue('warning',
                      u'DSSTI Facturas está en modo Demo',
                      reverse('company_accounts:company_profile_select_plan',
                              kwargs={'pk': self.id}),
                      u'Seleccionar Plan'))
        elif self.licence.expired:
            res.append(
                Issue('danger',
                      u'La licencia de DSSTI Facturas ha caducado',
                      reverse('company_accounts:company_profile',
                              kwargs={'pk': self.id})))
        elif self.licence.days_to_expiration < 10:
            res.append(
                Issue('warning',
                      u'Quedan pocos días para que caduque la licencia de DSSTI Facturas',
                      reverse('company_accounts:company_profile',
                              kwargs={'pk': self.id})))
        if not self.can_sign:
            res.append(
                Issue('danger',
                      u'No hay certificado para firmar los comprobantes electrónicos',
                      reverse('company_accounts:company_upload_cert',
                              kwargs={'pk': self.id}),
                      u"Subir Certificado")
            )
        for issue in CompanyIssue.objects.filter(company=self).exclude(fixed=True):
            res.append(
                Issue('danger',
                      issue.issue,
                      reverse('company_accounts:fix_issue',
                              kwargs={'pk': issue.id}),
                      u"Confirmar que ha sido arreglado")
            )
        
        return res

    def add_db_issue(self, issue_text):
        issue = CompanyIssue(
            company=self,
            issue=issue_text)
        issue.save()


class CompanyUser(models.Model):
    """
    Represents a shop clerk that has an associated company and user account
    He can log in and user the facilities for the associated company
    """
    company = models.ForeignKey(Company)
    user = models.ForeignKey(User)

    def __unicode__(self):
        return self.user.username


class CompanyIssue(models.Model):
    """
    List of issues on a company
    """
    company = models.ForeignKey(Company)
    issue = models.CharField(max_length=500)
    fixed = models.BooleanField(default=False)


class Establecimiento(models.Model):
    """
    Represents a shop owned by the company
    """
    company = models.ForeignKey(Company)
    descripcion = models.CharField(max_length=50)
    codigo = models.CharField(max_length=3)
    direccion = models.CharField(max_length=100)

    @property
    def puntos_emision(self):
        return PuntoEmision.objects.filter(establecimiento=self)

    def __unicode__(self):
        return self.descripcion


class PuntoEmision(models.Model):
    """
    Represents a cashing machine where bills are being emitted
    """
    establecimiento = models.ForeignKey(Establecimiento)
    descripcion = models.CharField(max_length=50)
    codigo = models.CharField(max_length=3)
    siguiente_secuencial_pruebas = models.IntegerField(default=1)
    siguiente_secuencial_produccion = models.IntegerField(default=1)
    ambiente_sri = models.CharField(
        max_length=20,
        choices=ambiente_sri_OPTIONS,
        default="pruebas")  # FIXME: default=produccion

    @property
    def siguiente_secuencial(self):
        ambiente = self.ambiente_sri
        if ambiente == 'pruebas':
            return self.siguiente_secuencial_pruebas
        elif ambiente == 'produccion':
            return self.siguiente_secuencial_produccion
        else:
            raise Exception("Unknown ambiente_sri: {}".format(ambiente))

    @siguiente_secuencial.setter
    def siguiente_secuencial(self, newval):
        ambiente = self.ambiente_sri
        if ambiente == 'pruebas':
            self.siguiente_secuencial_pruebas = newval
        elif ambiente == 'produccion':
            self.siguiente_secuencial_produccion = newval
        else:
            raise Exception("Unknown ambiente_sri: {}".format(ambiente))

    def get_absolute_url(self):
        return reverse("company_accounts:punto_emision_detail",
                       kwargs={'pk': self.pk})


class BannedCompany(models.Model):
    """
    Represents a company that is not welcome to the system
    """
    ruc = models.CharField(max_length=20)
    reason = models.TextField()


class ReadOnlyModelMixin(object):
    def save(self, *args, **kwargs):
        if not self.id:
            return super(ReadOnlyModelMixin, self).save(*args, **kwargs)
        else:
            raise Exception("{} can't be altered"
                            .format(self.__class__.__name__))

    def delete(self, *args, **kwargs):
        raise Exception("{} can't be deleted"
                        .format(self.__class__.__name__))


class LicenceHistory(ReadOnlyModelMixin, models.Model):
    """
    Changes to licences
    """
    licence = models.ForeignKey(Licence)
    date = models.DateField()
    action = models.TextField()

    @property
    def company(self):
        return self.licence.company

    def __unicode__(self):
        try:
            company = self.licence.company
        except:
            company = None
        return u"Licence History {date}: {licence} {company} {action}".format(
            date=self.date,
            licence=self.licence,
            action=self.action,
            company=company)


class LicenceUpdateRequest(models.Model):
    """
    Changes to licences
    """
    licence = models.ForeignKey(Licence)
    date = models.DateField()
    action = models.TextField()
    result = models.TextField(blank=True)

    def save(self, *args, **kwargs):
        action = {"action": "update request",
                  'user_viewable': True,
                  "date": str(self.date),
                  "action": json.loads(self.action),
                  }
        if self.result:
            action['result'] = json.loads(self.result),
        LicenceHistory(
            licence=self.licence,
            date=datetime.now(tz=pytz.timezone('America/Guayaquil')),
            action=json.dumps(action)
            ).save()
        super(LicenceUpdateRequest, self).save(*args, **kwargs)
