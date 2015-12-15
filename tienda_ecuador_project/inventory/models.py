# * encoding: utf-8 *
from datetime import date
from decimal import Decimal

from django.db import models
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

import company_accounts.models
from sri.models import Tax, Iva, Ice


Item_tipo_OPTIONS = (
    ('producto', 'Producto'),
    ('servicio', 'Servicio'),
)


Item_decimales_OPTIONS = (
    (0, 'Unidades Enteras'),
    (1, '1 Decimal'),
    (2, '2 Decimales'),
    (3, '3 Decimales'),
)


class Item(models.Model):
    """
    Represents an item that can be sold or bought
    """
    name = models.CharField(max_length=50)
    code = models.CharField(max_length=50)
    description = models.CharField(max_length=500, blank=True)
    tax_items = models.ManyToManyField(Tax)
    tipo = models.CharField(
        max_length=10,
        choices=Item_tipo_OPTIONS)
    decimales_qty = models.IntegerField(
        max_length=1,
        choices=Item_decimales_OPTIONS,
        default=0)
    company = models.ForeignKey(company_accounts.models.Company)

    @property
    def taxes(self):
        """
        Returns the properly typed tax items
        """
        def typecast(v):
            for t in [Iva, Ice]:
                try:
                    return t.objects.get(id=v.id)
                except t.DoesNotExist:
                    pass
        return map(typecast, self.tax_items.all())

    @property
    def ice(self):
        for i in self.taxes:
            if type(i) == Ice:
                return i

    @property
    def iva(self):
        for i in self.taxes:
            if type(i) == Iva:
                return i
        else:
            raise Exception("Error: No IVA")

    @property
    def increment_qty(self):
        return "{}".format(1 / (Decimal("10") ** self.decimales_qty))

    def __unicode__(self):
        return u"{} - {}".format(self.code, self.name)


class Batch(models.Model):
    """
    Represents a bunch of items that were bought some date
    """
    item = models.ForeignKey(Item)
    unit_cost = models.DecimalField(max_digits=20, decimal_places=8)
    code = models.CharField(max_length=50)
    acquisition_date = models.DateField()


class SKU(models.Model):
    """
    Represents an item or group of items from the same batch
    that are stored on an Establecimiento
    """
    batch = models.ForeignKey(Batch)
    qty = models.DecimalField(max_digits=20, decimal_places=8)
    unit_price = models.DecimalField(max_digits=20, decimal_places=8)
    establecimiento = models.ForeignKey(company_accounts.models.Establecimiento)
    # Where on the store it is located
    location = models.CharField(
        max_length=500)
