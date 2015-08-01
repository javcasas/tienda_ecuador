# * encoding: utf8 *
from decimal import Decimal

from django.db import models
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

from utils import Property, ConvertedProperty
from validators import OneOf, IsCedula, IsRuc


class ReadOnlyObject(Exception):
    """
    Exception for when trying to write read-only objects
    """


class ReadOnlyMixin(object):
    """
    A mixin that disables overwriting or deleting objects
    """
    def save(self, *args, **kwargs):
        """
        Disable save
        """
        if self.id:
            raise ReadOnlyObject("{} can't be saved".format(self.__class__))
        else:
            return models.Model.save(self, *args, **kwargs)

    def secret_save(self, *args, **kwargs):
        """
        Secret save does save
        """
        return models.Model.save(self, *args, **kwargs)

    def delete(self, *args, **kwargs):
        """
        Disable delete
        """
        raise ReadOnlyObject("{} can't be deleted".format(self.__class__))

    def secret_delete(self, *args, **kwargs):
        """
        Secret delete does delete
        """
        return models.Model.delete(self, *args, **kwargs)


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
        validators=[OneOf("pruebas", "produccion")],
        default="pruebas")
    siguiente_comprobante_pruebas = models.IntegerField(default=1)
    siguiente_comprobante_produccion = models.IntegerField(default=1)
    cert = models.CharField(max_length=20000, blank=True)
    key = models.CharField(max_length=100, blank=True)

    def __unicode__(self):
        return self.razon_social


class CompanyUser(models.Model):
    """
    Represents a shop clerk that has an associated company and user account
    He can log in and user the facilities for the associated company
    """
    company = models.ForeignKey(Company)
    user = models.ForeignKey(User)

    def __unicode__(self):
        return self.user.username


##################################
# Customers
##################################
class BaseCustomer(models.Model):
    """
    Represents a generic customer
    """
    razon_social = models.CharField(max_length=100)
    tipo_identificacion = models.CharField(
        max_length=100,
        validators=[OneOf('cedula', 'ruc', 'pasaporte')])
    identificacion = models.CharField(max_length=100)
    email = models.CharField(max_length=100, blank=True)
    direccion = models.CharField(max_length=100, blank=True)

    def __unicode__(self):
        return "({}){} - {}".format(self.tipo_identificacion,
                                    self.identificacion,
                                    self.razon_social)

    def clean(self):
        if self.tipo_identificacion == "ruc":
            IsRuc(self.identificacion)
        elif self.tipo_identificacion == 'cedula':
            IsCedula(self.identificacion)
        else:
            raise ValidationError("Identificacion desconocida")

    def save(self, *args, **kwargs):
        self.clean()
        return super(BaseCustomer, self).save(*args, **kwargs)


class Customer(BaseCustomer):
    """
    Represents a generic customer
    """
    company = models.ForeignKey(Company)

    def get_absolute_url(self):
        return reverse('customer_detail',
                       kwargs={'company_id': self.company.id, 'pk': self.pk})


class BillCustomer(ReadOnlyMixin, BaseCustomer):
    """
    A customer in a final bill
    """
    @classmethod
    def fromCustomer(cls, c):
        fields = ['razon_social', 'tipo_identificacion', 'identificacion',
                  'email', 'direccion']
        data = {}
        for field in fields:
            data[field] = getattr(c, field)
        new = BillCustomer(**data)
        new.secret_save()
        return new


#####################################
# Bill
#####################################
class BaseBill(models.Model):
    """
    Represents a generic bill
    """
    number = models.CharField(max_length=20, blank=True)
    company = models.ForeignKey(Company)
    date = models.DateTimeField()

    def __unicode__(self):
        return "{} - {}".format(self.number, self.issued_to)


class Bill(ReadOnlyMixin, BaseBill):
    """
    Represents a bill
    """
    issued_to = models.ForeignKey(BillCustomer)

    @classmethod
    def fromProformaBill(cls, proforma):
        customer = BillCustomer.fromCustomer(proforma.issued_to)
        fields = ['number', 'company', 'date']
        data = {}
        for field in fields:
            data[field] = getattr(proforma, field)
        data['issued_to'] = customer
        new = Bill(**data)
        new.secret_save()
        for proformaitem in proforma.items:
            item = BillItem.fromProformaBillItem(proformaitem, bill=new)
            item.secret_save()
        return new

    @property
    def items(self):
        return BillItem.objects.filter(bill=self)


class ClaveAcceso(object):
    def fecha_emision_validator(v):
        from datetime import date
        try:
            y, m, d = v
            date(y, m, d)
            return True
        except Exception:
            return False

    fecha_emision = Property(fecha_emision_validator)
    ruc = Property()
    serie = Property()
    numero = Property()
    codigo = Property()

    tipo_comprobante = ConvertedProperty(factura='01')
    ambiente = ConvertedProperty(pruebas='1', produccion='2')
    tipo_emision = ConvertedProperty(normal='1', offline='2')

    def __unicode__(self):
        codigo = (u"{2:02d}{1:02d}{0:04d}".format(*self.fecha_emision) +
                  self.tipo_comprobante.code +
                  self.ruc +
                  self.ambiente.code +
                  "{:06d}".format(self.serie) +
                  "{:09d}".format(self.numero) +
                  "{:08d}".format(self.codigo) +
                  self.tipo_emision.code)

        def comprobante(c):
            rev_c = c[::-1]
            multipliers = "234567" * 10
            pairs = zip(rev_c, multipliers)
            products = map(lambda (a, b): int(a) * int(b), pairs)
            total = sum(products)
            modulus = total % 11
            if modulus == 0:
                return "0"
            elif modulus == 1:
                return "1"
            else:
                return str(11 - modulus)
        res = codigo + comprobante(codigo)
        return res


class ProformaBill(BaseBill):
    """
    Represents a proforma bill
    """
    issued_to = models.ForeignKey(Customer)

    @property
    def items(self):
        return ProformaBillItem.objects.filter(proforma_bill=self)

    @property
    def subtotal(self):
        res = {0: 0,
               12: 0}
        for i in self.items:
            res[i.iva.porcentaje] = (res.get(i.iva.porcentaje, 0) +
                                     i.total_sin_impuestos + i.valor_ice)
        return res

    @property
    def iva(self):
        res = {}
        for item in self.items:
            iva = item.iva.porcentaje
            res[iva] = res.get(iva, 0) + item.valor_iva
        return res

    @property
    def total_sin_impuestos(self):
        return sum([i.total_sin_impuestos for i in self.items])

    @property
    def total_con_impuestos(self):
        return sum([(i.total_sin_impuestos + i.valor_ice + i.valor_iva) for i in self.items])

    @property
    def impuestos(self):
        # key: (codigo, codigo_porcentaje, porcentaje)
        # value: (base_imponible, valor)
        from operator import add
        accum = {}
        for item in self.items:
            k = ("2", item.iva.codigo, item.iva.porcentaje)
            accum[k] = map(sum,
                           zip(accum.get(k, (0, 0)),
                               (item.base_imponible_iva, item.valor_iva)))
            if item.ice:
                k = ("3", item.ice.codigo, item.ice.porcentaje)
                accum[k] = map(sum,
                               zip(accum.get(k, (0, 0)),
                                   (item.base_imponible_ice, item.valor_ice)))

        return [
            {
                "codigo": codigo,
                "codigo_porcentaje": codigo_porcentaje,
                "porcentaje": porcentaje,
                "base_imponible": base_imponible,
                "valor": valor,
            } for ((codigo, codigo_porcentaje, porcentaje), (base_imponible, valor))
              in sorted(accum.iteritems())
        ]

    @property
    def total(self):
        iva = self.iva
        total_impuestos = sum([iva[k] for k in iva])
        subtotal = self.subtotal
        total_subtotales = sum([subtotal[k] for k in self.subtotal])
        return total_subtotales + total_impuestos

    def get_absolute_url(self):
        return reverse('proformabill_detail',
                       kwargs={'company_id': self.company.id, 'pk': self.pk})

    def __unicode__(self):
        try:
            return "{} - {}".format(self.number, self.issued_to)
        except:
            return "{} - {}".format(self.number, "<Not set>")


##########################
# Taxes
##########################
class Iva(models.Model):
    """
    Representa el IVA
    """
    descripcion = models.CharField(max_length=50)
    codigo = models.CharField(max_length=10)
    porcentaje = models.DecimalField(decimal_places=2, max_digits=6)

    def __unicode__(self):
        return "{:.0f}% - {}".format(self.porcentaje, self.descripcion)


class BillItemIva(ReadOnlyMixin, Iva):
    """
    IVA para items cerrados
    """
    @classmethod
    def fromIva(cls, iva):
        fields = ['descripcion', 'codigo', 'porcentaje']
        data = {k: getattr(iva, k) for k in fields}
        new, created = BillItemIva.objects.get_or_create(**data)
        return new


class Ice(models.Model):
    """
    Representa el ICE
    """
    descripcion = models.CharField(max_length=50)
    grupo = models.IntegerField()
    codigo = models.CharField(max_length=10)
    porcentaje = models.DecimalField(decimal_places=2, max_digits=6)

    def __nonzero__(self):
        return self.descripcion != "No ICE"

    def __unicode__(self):
        return "{:.0f}% - {}".format(self.porcentaje, self.descripcion)


class BillItemIce(ReadOnlyMixin, Ice):
    """
    ICE para items cerrados
    """
    @classmethod
    def fromIce(cls, ice):
        fields = ['descripcion', 'grupo', 'codigo', 'porcentaje']
        data = {k: getattr(ice, k) for k in fields}
        new, created = BillItemIce.objects.get_or_create(**data)
        return new


###########################
# Items
##########################
class BaseItem(models.Model):
    """
    Represents an abstract stock item
    """
    sku = models.CharField(max_length=50)
    name = models.CharField(max_length=50)
    description = models.CharField(max_length=500)
    unit_cost = models.DecimalField(max_digits=20, decimal_places=8)
    unit_price = models.DecimalField(max_digits=20, decimal_places=8)


class Item(BaseItem):
    """
    Represents an item that can be sold or bought
    """
    company = models.ForeignKey(Company)
    iva = models.ForeignKey(Iva)
    ice = models.ForeignKey(Ice)

    def get_absolute_url(self):
        return reverse('item_detail',
                       kwargs={'company_id': self.company.id, 'pk': self.pk})

    def __unicode__(self):
        return "{} - {}".format(self.sku, self.name)


class ItemInBill(BaseItem):
    """
    Base class for items that are part of a bill
    """
    qty = models.DecimalField(max_digits=20, decimal_places=8)

    @property
    def total_sin_impuestos(self):
        return self.qty * self.unit_price

    @property
    def valor_ice(self):
        return (self.total_sin_impuestos *
                (self.ice.porcentaje / Decimal("100.0")))

    @property
    def valor_iva(self):
        return (self.base_imponible_iva *
                (self.iva.porcentaje / Decimal("100.0")))

    @property
    def base_imponible_iva(self):
        return self.total_sin_impuestos + self.valor_ice

    @property
    def base_imponible_ice(self):
        return self.total_sin_impuestos

    @property
    def total_impuestos(self):
        return self.valor_ice + self.valor_iva


class ProformaBillItem(ItemInBill):
    """
    Represents an item in a proforma bill
    """
    proforma_bill = models.ForeignKey(ProformaBill)
    iva = models.ForeignKey(Iva)
    ice = models.ForeignKey(Ice)


class BillItem(ReadOnlyMixin, ItemInBill):
    """
    Represents an item in a final bill
    """
    bill = models.ForeignKey(Bill)
    iva = models.ForeignKey(BillItemIva)
    ice = models.ForeignKey(BillItemIce)

    @classmethod
    def fromProformaBillItem(self, billitem, bill):
        fields = ['sku', 'name', 'description', 'qty',
                  'unit_cost', 'unit_price']
        data = {}
        for field in fields:
            data[field] = getattr(billitem, field)
        data['bill'] = bill
        data['iva'] = BillItemIva.fromIva(billitem.iva)
        data['ice'] = BillItemIce.fromIce(billitem.ice)
        new = BillItem(**data)
        new.secret_save()
        return new
