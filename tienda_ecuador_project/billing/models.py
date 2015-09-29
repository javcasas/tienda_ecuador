# * encoding: utf8 *
from datetime import date
from decimal import Decimal

from django.db import models
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

from utils import Property, ConvertedProperty
from validators import IsCedula, IsRuc


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
    licencia = models.CharField(
        max_length=20,
        choices=Company_licencia_OPTIONS,
        default="demo")
    siguiente_numero_proforma = models.IntegerField(default=1)
    logo = models.ImageField(upload_to='company_logos', blank=True)
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


##################################
# Customers
##################################
BaseCustomer_tipo_identificacion_OPTIONS = (
    ('cedula', 'Cédula'),
    ('ruc', 'RUC'),
    ('pasaporte', 'Pasaporte'),
)


class BaseCustomer(models.Model):
    """
    Represents a generic customer
    """
    razon_social = models.CharField(max_length=100)
    tipo_identificacion = models.CharField(
        max_length=100,
        choices=BaseCustomer_tipo_identificacion_OPTIONS)
    identificacion = models.CharField(max_length=100)
    email = models.CharField(max_length=100, blank=True)
    direccion = models.CharField(max_length=100, blank=True)

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
        return super(BaseCustomer, self).save(*args, **kwargs)


class Customer(BaseCustomer):
    """
    Represents a generic customer
    """
    company = models.ForeignKey(Company)

    def get_absolute_url(self):
        return reverse('customer_detail',
                       kwargs={'pk': self.pk})


#####################################
# Bill
#####################################
class BaseBill(models.Model):
    """
    Represents a generic bill
    """
    number = models.CharField(max_length=20, blank=True)
    date = models.DateTimeField()
    xml_content = models.TextField(blank=True)
    ride_content = models.TextField(blank=True)

    def __unicode__(self):
        return u"{} - {}".format(self.number, self.date)

    def __eq__(self, other):
        try:
            if not isinstance(other, BaseBill):
                return False
            return other.id == self.id
        except:
            return False


class Bill(ReadOnlyMixin, BaseBill):
    """
    Represents a bill
    """
    company = models.ForeignKey(Company)

    copy_from_fields = ['number', 'date', 'xml_content', 'ride_content']

    @classmethod
    def fromProformaBill(cls, proforma):
        data = {}
        for field in cls.copy_from_fields:
            data[field] = getattr(proforma, field)
        data['company'] = proforma.punto_emision.establecimiento.company
        new = Bill(**data)
        new.secret_save()
        return new


class ClaveAcceso(object):
    def fecha_emision_validator(v):
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

    @classmethod
    def comprobante(self, c):
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

    def __unicode__(self):
        codigo = (u"{2:02d}{1:02d}{0:04d}".format(*self.fecha_emision) +
                  self.tipo_comprobante.code +
                  self.ruc +
                  self.ambiente.code +
                  "{:06d}".format(self.serie) +
                  "{:09d}".format(self.numero) +
                  "{:08d}".format(self.codigo) +
                  self.tipo_emision.code)

        res = codigo + self.comprobante(codigo)
        return res


class ProformaBill(BaseBill):
    """
    Represents a proforma bill
    """
    issued_to = models.ForeignKey(Customer, null=True, blank=True)
    punto_emision = models.ForeignKey(PuntoEmision)
    secuencial_pruebas = models.IntegerField(default=0, blank=True)
    secuencial_produccion = models.IntegerField(default=0, blank=True)

    @property
    def items(self):
        return ProformaBillItem.objects.filter(proforma_bill=self)

    @property
    def subtotal(self):
        res = {0: Decimal(0),
               12: Decimal(0)}
        for i in self.items:
            res[i.iva.porcentaje] = (res.get(i.iva.porcentaje, 0) +
                                     i.total_sin_impuestos + i.valor_ice)
        return res

    @property
    def iva(self):
        res = {
            Decimal(12): Decimal(0),
            Decimal(0): Decimal(0),
        }
        for item in self.items:
            iva = item.iva.porcentaje
            res[iva] = res[iva] + item.valor_iva
        return res

    @property
    def total_sin_impuestos(self):
        return sum([i.total_sin_impuestos for i in self.items])

    @property
    def total_con_impuestos(self):
        return sum([(i.total_sin_impuestos + i.valor_ice + i.valor_iva)
                    for i in self.items])

    @property
    def impuestos(self):
        # key: (codigo, codigo_porcentaje, porcentaje)
        # value: (base_imponible, valor)
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
            } for ((codigo, codigo_porcentaje, porcentaje),
                   (base_imponible, valor))
            in sorted(accum.iteritems())
        ]

    @property
    def total(self):
        iva = self.iva
        total_impuestos = sum([iva[k] for k in iva])
        subtotal = self.subtotal
        total_subtotales = sum([subtotal[k] for k in self.subtotal])
        return total_subtotales + total_impuestos

    @property
    def payment(self):
        return Pago.objects.filter(proforma_bill_id=self.id)

    @property
    def secuencial(self):
        ambiente = self.punto_emision.establecimiento.company.ambiente_sri
        if ambiente == 'pruebas':
            return self.secuencial_pruebas
        elif ambiente == 'produccion':
            return self.secuencial_produccion
        else:
            raise Exception("Unknown ambiente_sri: {}".format(ambiente))

    @secuencial.setter
    def secuencial(self, newval):
        ambiente = self.punto_emision.establecimiento.company.ambiente_sri
        if ambiente == 'pruebas':
            self.secuencial_pruebas = newval
        elif ambiente == 'produccion':
            self.secuencial_produccion = newval
        else:
            raise Exception("Unknown ambiente_sri: {}".format(ambiente))

    def get_absolute_url(self):
        return reverse('proformabill_detail',
                       kwargs={'pk': self.pk})

    def __unicode__(self):
        return u"{} - {}".format(self.number, self.issued_to)


##########################
# Taxes
##########################
class Tax(models.Model):
    descripcion = models.CharField(max_length=100)
    codigo = models.CharField(max_length=10)
    porcentaje = models.DecimalField(decimal_places=2, max_digits=6)
    valor_fijo = models.DecimalField(
        decimal_places=2, max_digits=6, default=Decimal('0.00'))


class Iva(Tax):
    """
    Representa el IVA
    """
    def __unicode__(self):
        return u"{:.0f}% - {}".format(self.porcentaje, self.descripcion)


class Ice(Tax):
    """
    Representa el ICE
    """
    grupo = models.IntegerField()

    def __nonzero__(self):
        return self.descripcion != "No ICE"

    def __unicode__(self):
        return u"{:.0f}% - {}".format(self.porcentaje, self.descripcion)


###########################
# Items
##########################
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


class BaseItem(models.Model):
    """
    Represents an abstract stock item
    """
    sku = models.CharField(max_length=50)
    name = models.CharField(max_length=50)
    description = models.CharField(max_length=500)
    unit_cost = models.DecimalField(max_digits=20, decimal_places=8)
    unit_price = models.DecimalField(max_digits=20, decimal_places=8)
    tax_items = models.ManyToManyField(Tax)
    tipo = models.CharField(
        max_length=10,
        choices=Item_tipo_OPTIONS)
    decimales_qty = models.IntegerField(
        max_length=1,
        choices=Item_decimales_OPTIONS,
        default=0)

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


class Item(BaseItem):
    """
    Represents an item that can be sold or bought
    """
    company = models.ForeignKey(Company)

    def get_absolute_url(self):
        return reverse('item_detail',
                       kwargs={'pk': self.pk})

    def __unicode__(self):
        return u"{} - {}".format(self.sku, self.name)


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


############################################
# Pagos
############################################
class FormaPago(models.Model):
    """
    Formas de pago
    """
    codigo = models.CharField(max_length=2)
    descripcion = models.CharField(max_length=50)

    def __unicode__(self):
        return u"{}".format(self.descripcion)


class PlazoPago(models.Model):
    """
    Plazos de pago
    """
    descripcion = models.CharField(max_length=50)
    unidad_tiempo = models.CharField(max_length=20)
    tiempo = models.IntegerField()

    def __unicode__(self):
        return u"{} ({} {})".format(self.descripcion,
                                    self.tiempo,
                                    self.unidad_tiempo)


class Pago(models.Model):
    """
    Pagos en una factura
    """
    porcentaje = models.DecimalField(max_digits=20, decimal_places=8)
    forma_pago = models.ForeignKey(FormaPago)
    plazo_pago = models.ForeignKey(PlazoPago)
    proforma_bill = models.ForeignKey(ProformaBill)

    @property
    def cantidad(self):
        return (self.porcentaje * self.proforma_bill.total_con_impuestos) / Decimal(100)
