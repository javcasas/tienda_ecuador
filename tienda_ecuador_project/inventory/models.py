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
    name = models.CharField(max_length=100)
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
    unit_cost = models.DecimalField(max_digits=20, decimal_places=4)
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
    qty = models.DecimalField(max_digits=20, decimal_places=4)
    qty_unlimited = models.BooleanField(default=False)
    unit_price = models.DecimalField(max_digits=20, decimal_places=4)
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

    def substract(self, qty):
        if not self.qty_unlimited:
            self.qty -= qty
            self.save()

    def get_absolute_url(self):
        return reverse("sku_detail", args=(self.id,))

    def __unicode__(self):
        if self.qty_unlimited:
            return self.batch.item.name
        else:
            fmt_string = u"{:." + unicode(self.batch.item.decimales_qty) + u"f} x {}"
            return fmt_string.format(self.qty, self.batch.item.name)

    @property
    def margin(self):
        return self.unit_price - self.batch.unit_cost

    @property
    def margin_percent(self):
        cost = self.batch.unit_cost
        if cost == 0:
            return Decimal(100)
        price = self.unit_price
        return ((price/cost) - 1) * 100

    @property
    def warnings(self):
        res = {}
        if self.qty <= 0:
            res['qty'] = 'danger'
        elif self.qty <= 10:
            res['qty'] = 'warning'

        if self.margin_percent < 10:
            res['margin'] = 'danger'
        elif self.margin_percent < 50:
            res['margin'] = 'warning'
        return res

    @property
    def css_warnings(self):
        return {key: 'bg-' + val for key, val in self.warnings.iteritems()}

    @property
    def decimales_qty(self):
        return self.batch.item.decimales_qty

    def can_be_sold(self, ammount=1):
        return self.unlimited_qty or self.qty >= ammount
