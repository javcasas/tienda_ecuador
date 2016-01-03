# * encoding: utf-8 *
from decimal import Decimal

from django.db import models
from django.core.urlresolvers import reverse

import company_accounts.models
from sri.models import Tax, Iva, Ice

from util.enum import Enum
import purchases.models


ItemTipo = Enum(
    "ItemTipo",
    (
        ('producto', 'Producto (ej. papas, muebles, televisores)'),
        ('servicio', 'Servicio (ej. reparación, transporte, instalación)'),
    )
)


ItemDecimales = Enum(
    "ItemDecimales",
    (
        (0, 'El artículo se vende por unidades enteras'),
        (2, 'El artículo se vende por décimas partes'),
        (2, 'El artículo se vende por centésimas partes (centímetros)'),
        (3, 'El artículo se vende por milésimas partes (gramos, milímetros)'),
    )
)


class Item(models.Model):
    """
    Represents an item that can be sold or bought
    """
    name = models.CharField(max_length=50)
    code = models.CharField(max_length=50)
    distributor_code = models.CharField(max_length=50, blank=True)
    description = models.CharField(max_length=500, blank=True)
    tax_items = models.ManyToManyField(Tax)
    tipo = models.CharField(
        max_length=10,
        choices=ItemTipo.__OPTIONS__)
    decimales_qty = models.IntegerField(
        choices=ItemDecimales.__OPTIONS__,
        default=0)
    company = models.ForeignKey(company_accounts.models.Company)

    class Meta:
        unique_together = (("company", "code"),)

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

    def get_absolute_url(self):
        return reverse("item_detail", args=(self.id,))

    @property
    def batches(self):
        return Batch.objects.filter(item=self)


class Batch(models.Model):
    """
    Represents a bunch of items that were bought some date
    """
    item = models.ForeignKey(Item)
    unit_cost = models.DecimalField(max_digits=20, decimal_places=8)
    code = models.IntegerField()
    acquisition_date = models.DateField()
    purchase = models.ForeignKey(purchases.models.Purchase, blank=True, null=True)

    class Meta:
        unique_together = (("item", "code"),)

    def get_absolute_url(self):
        return reverse("batch_detail", args=(self.id,))

    @property
    def skus(self):
        return SKU.objects.filter(batch=self)

    def __unicode__(self):
        return u"{}-{}".format(self.item.code, self.code)


class SKU(models.Model):
    """
    Represents an item or group of items from the same batch
    that are stored on an Establecimiento
    """
    batch = models.ForeignKey(Batch)
    qty = models.DecimalField(max_digits=20, decimal_places=8)
    unit_price = models.DecimalField(max_digits=20, decimal_places=8)
    establecimiento = models.ForeignKey(
        company_accounts.models.Establecimiento)
    # Where on the store it is located
    location = models.CharField(
        max_length=500)

    class Meta:
        unique_together = (("batch", "establecimiento"),)

    @property
    def code(self):
        return u"{}-{}".format(self.batch.item.code, self.batch.code)

    @property
    def name(self):
        return self.batch.item.name

    def get_absolute_url(self):
        return reverse("sku_detail", args=(self.id,))

    def __unicode__(self):
        fmt_string = u"{:." + unicode(self.batch.item.decimales_qty) + u"f} x {}"
        return fmt_string.format(self.qty, self.batch.item.name)
