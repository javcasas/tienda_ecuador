# * encoding: utf-8 *
from django.db import models
from django.core.urlresolvers import reverse

from util.validators import IsCedula, IsRuc
from django.core.exceptions import ValidationError
from company_accounts.models import Company

from util.enum import Enum


TipoIdentificacion = Enum(
    "TipoIdentificacion",
    (
        ('cedula', 'Cédula'),
        ('ruc', 'RUC'),
        ('pasaporte', 'Pasaporte'),
    )
)


class Customer(models.Model):
    """
    Represents a generic customer
    """
    razon_social = models.CharField(max_length=100)
    tipo_identificacion = models.CharField(
        max_length=100,
        choices=TipoIdentificacion.__OPTIONS__)
    identificacion = models.CharField(max_length=100)
    email = models.CharField(max_length=100, blank=True)
    direccion = models.CharField(max_length=100, blank=True)
    company = models.ForeignKey(Company)

    def __unicode__(self):
        return u"{}({})".format(self.razon_social,
                                self.identificacion)

    def clean(self):
        if self.tipo_identificacion == "ruc":
            IsRuc(self.identificacion)
        elif self.tipo_identificacion == 'cedula':
            IsCedula(self.identificacion)
        else:
            raise ValidationError("Identificacion desconocida")

    def save(self, *args, **kwargs):
        self.clean()
        return super(Customer, self).save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('customer_detail',
                       kwargs={'pk': self.pk})
