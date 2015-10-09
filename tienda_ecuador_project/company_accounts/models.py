# * encoding: utf8 *
from datetime import date, timedelta

from django.db import models
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User


Company_ambiente_sri_OPTIONS = (
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

    def approve(self, next_licence, new_date):
        """
        Approve the next licence with the new expiration date
        """
        self.licence = next_licence
        self.expiration = new_date
        self.save()

    def __unicode__(self):
        return dict(Company_licencia_OPTIONS)[self.licence]


def default_licence():
    n = Licence()
    n.save()
    return n.id


class Company(models.Model):
    """
    Represents a company
    """
    nombre_comercial = models.CharField(max_length=100, unique=True)
    ruc = models.CharField(max_length=100, unique=True)
    razon_social = models.CharField(max_length=100, unique=True)
    direccion_matriz = models.CharField(max_length=100)
    contribuyente_especial = models.CharField(max_length=20, blank=True)
    obligado_contabilidad = models.BooleanField(default=False)
    ambiente_sri = models.CharField(
        max_length=20,
        choices=Company_ambiente_sri_OPTIONS,
        default="pruebas")
    licence = models.ForeignKey(Licence, default=default_licence)
    siguiente_numero_proforma = models.IntegerField(default=1)
    logo = models.ImageField(upload_to='company_logos', blank=True)
    cert = models.CharField(max_length=20000, blank=True)
    key = models.CharField(max_length=100, blank=True)

    def __unicode__(self):
        return self.razon_social

    def get_absolute_url(self):
        return reverse("company_accounts:company_profile", kwargs={'pk': self.pk})


class CompanyUser(models.Model):
    """
    Represents a shop clerk that has an associated company and user account
    He can log in and user the facilities for the associated company
    """
    company = models.ForeignKey(Company)
    user = models.ForeignKey(User)

    def __unicode__(self):
        return self.user.username


class Establecimiento(models.Model):
    """
    Represents a shop owned by the company
    """
    company = models.ForeignKey(Company)
    descripcion = models.CharField(max_length=50)
    codigo = models.CharField(max_length=3)
    direccion = models.CharField(max_length=100)


class PuntoEmision(models.Model):
    """
    Represents a cashing machine where bills are being emitted
    """
    establecimiento = models.ForeignKey(Establecimiento)
    descripcion = models.CharField(max_length=50)
    codigo = models.CharField(max_length=3)
    siguiente_secuencial_pruebas = models.IntegerField(default=1)
    siguiente_secuencial_produccion = models.IntegerField(default=1)

    @property
    def siguiente_secuencial(self):
        ambiente = self.establecimiento.company.ambiente_sri
        if ambiente == 'pruebas':
            return self.siguiente_secuencial_pruebas
        elif ambiente == 'produccion':
            return self.siguiente_secuencial_produccion
        else:
            raise Exception("Unknown ambiente_sri: {}".format(ambiente))

    @siguiente_secuencial.setter
    def siguiente_secuencial(self, newval):
        ambiente = self.establecimiento.company.ambiente_sri
        if ambiente == 'pruebas':
            self.siguiente_secuencial_pruebas = newval
        elif ambiente == 'produccion':
            self.siguiente_secuencial_produccion = newval
        else:
            raise Exception("Unknown ambiente_sri: {}".format(ambiente))


