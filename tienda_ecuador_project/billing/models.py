# * encoding: utf-8 *
from datetime import date, timedelta
from decimal import Decimal
import xml.etree.ElementTree as ET
import pytz

from django.db import models, transaction
from django.core.urlresolvers import reverse
from django.core.exceptions import ValidationError
from django.shortcuts import render_to_response

from util.property import Property, ConvertedProperty, ProtectedSetattr
from util import signature

from company_accounts.models import Company, PuntoEmision
from stakeholders.models import Customer
from inventory.models import SKU
from sri.models import ComprobanteSRIMixin, SRIStatus


class ReadOnlyObject(Exception):
    """
    Exception for when trying to write read-only objects
    """


#####################################
# Bill
#####################################
class Bill(ComprobanteSRIMixin, models.Model):
    """
    Represents a generic bill
    """
    number = models.CharField(max_length=20, blank=True)
    date = models.DateTimeField()
    company = models.ForeignKey(Company)
    issued_to = models.ForeignKey(Customer, null=True, blank=True)
    punto_emision = models.ForeignKey(PuntoEmision, null=True, blank=True)
    secuencial = models.IntegerField(default=0, blank=True)

    def __unicode__(self):
        return u"{} - {}".format(self.get_bill_number(), self.date.date())

    @property
    def items(self):
        return BillItem.objects.filter(bill=self)

    @property
    def receivables(self):
        import accounts_receivable.models
        return accounts_receivable.models.Receivable.objects.filter(bill=self)

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
    def total_sin_iva(self):
        return sum([(i.total_sin_impuestos + i.valor_ice)
                    for i in self.items])

    @property
    def total_ice(self):
        return sum(
            [item.valor_ice for item in self.items])

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
        return Pago.objects.filter(bill=self)

    def get_absolute_url(self):
        if self.status in [SRIStatus.options.NotSent, SRIStatus.options.Rejected]:
            return reverse('bill_detail',
                           kwargs={'pk': self.pk})
        else:
            return reverse('emitted_bill_detail',
                           kwargs={'pk': self.pk})

    def get_progress_url(self):
        if self.status == SRIStatus.options.ReadyToSend:
            return reverse('bill_emit_send_to_sri',
                           kwargs={'pk': self.pk})
        elif self.status == SRIStatus.options.Sent:
            return reverse('bill_emit_validate',
                           kwargs={'pk': self.pk})
        elif self.check_if_annulled_worthy():
            return reverse('bill_emit_check_annulled',
                           kwargs={'pk': self.pk})
        else:
            return None

    def accept(self):
        # Only decrease inventory when the bill goes from NotSent to ReadyToSend
        # not when it goes from Rejected to ReadyToSend
        decrease_inventory = self.status == SRIStatus.options.NotSent
        with transaction.atomic():
            res = super(Bill, self).accept()
            if decrease_inventory:
                for item in self.items:
                    item.substract_from_inventory()
        return res

    def validate_in_SRI(self):
        res = super(Bill, self).validate_in_SRI()
        if self.status == SRIStatus.options.Accepted:
            # Create receivables
            import accounts_receivable.models
            for payment in self.payment:
                if payment.plazo_pago.unidad_tiempo == 'dias':
                    payment_date = (self.date
                                    + timedelta(days=payment.plazo_pago.tiempo)).date()
                r = accounts_receivable.models.Receivable(
                    bill=self,
                    qty=payment.cantidad,
                    date=payment_date,
                    method=payment.forma_pago)
                r.save()
        return res

    def save(self, **kwargs):
        """
        Checks if there is payment
        """
        if self.status == SRIStatus.options.ReadyToSend:
            if not self.payment:
                raise ValidationError("No hay forma de pago")
        return super(Bill, self).save(**kwargs)

    def gen_pdf(self):
        from public_receipts import gen_ride
        return gen_ride.gen_bill_ride(self)

    def get_bill_number_from_xml(self):
        tree = ET.fromstring(self.xml_content.encode('utf8'))
        return u"{}-{}-{}".format(tree.find("./infoTributaria/estab").text,
                                  tree.find("./infoTributaria/ptoEmi").text,
                                  tree.find("./infoTributaria/secuencial").text)

    def get_bill_number(self):
        if self.status in [SRIStatus.options.NotSent, SRIStatus.options.ReadyToSend]:
            return self.number
        else:
            try:
                return self.get_bill_number_from_xml()
            except ET.ParseError:
                pass

    def gen_xml(self, codigo=None):
        """
        Generates XML content and clave de acceso
        Requires bill with:
            punto_emision
            ambiente_sri
            secuencial
            date
        @returns: signed_xml_content, clave_acceso
        """
        def get_code_from_proforma_number(number):
            for i in range(len(number)):
                try:
                    assert(int(number[i:]) >= 0)
                    assert(int(number[i:]) < 10 ** 8)
                    return int(number[i:])
                except (ValueError, AssertionError):
                    pass
            else:
                return 0

        assert self.punto_emision
        assert self.ambiente_sri
        assert self.secuencial
        assert self.date
        thedate = self.date.astimezone(pytz.timezone("America/Guayaquil"))

        company = self.punto_emision.establecimiento.company

        context = {
            'proformabill': self,
            'punto_emision': self.punto_emision,
            'establecimiento': self.punto_emision.establecimiento,
            'company': company,
        }

        context['secuencial'] = self.secuencial

        info_tributaria = {}
        info_tributaria['ambiente'] = {
            'pruebas': '1',
            'produccion': '2'
        }[self.ambiente_sri]

        info_tributaria['tipo_emision'] = '1'   # 1: normal
                                                # 2: indisponibilidad sistema
        info_tributaria['cod_doc'] = '01'   # 01: factura
                                            # 04: nota de credito
                                            # 05: nota de debito
                                            # 06: guia de remision
                                            # 07: comprobante de retencion
        c = ClaveAcceso()
        c.fecha_emision = (thedate.year,
                           thedate.month,
                           thedate.day)
        c.tipo_comprobante = "factura"
        c.ruc = str(company.ruc)
        c.ambiente = self.ambiente_sri
        c.establecimiento = int(self.punto_emision.establecimiento.codigo)
        c.punto_emision = int(self.punto_emision.codigo)
        c.numero = self.secuencial
        c.codigo = codigo or get_code_from_proforma_number(self.number)
        c.tipo_emision = "normal"
        clave_acceso = unicode(c)
        info_tributaria['clave_acceso'] = clave_acceso

        context['info_tributaria'] = info_tributaria

        info_factura = {}
        info_factura['tipo_identificacion_comprador'] = {    # tabla 7
            'ruc': '04',
            'cedula': '05',
            'pasaporte': '06',
            'consumidor_final': '07',
            'exterior': '08',
            'placa': '09',
        }[self.issued_to.tipo_identificacion]
        info_factura['total_descuento'] = sum([i.discount for i in self.items])
        info_factura['propina'] = 0             # No hay propinas
        info_factura['moneda'] = 'DOLAR'
        context['info_factura'] = info_factura

        context['info_adicional'] = {
            'Generado Con': 'DSSTI Facturas',
            'Web': 'http://facturas.dssti.com',
        }

        response = render_to_response("billing/proformabill_xml.html", context)

        xml_content = response.content
        # sign xml_content
        signed_xml_content = signature.sign(company.ruc, company.id, xml_content)
        return signed_xml_content, clave_acceso


class ClaveAcceso(ProtectedSetattr):
    def fecha_emision_validator(v):
        try:
            y, m, d = v
            date(y, m, d)
            return True
        except Exception:
            return False

    def max_digits_validator(number):
        def validator(v):
            limit = 10 ** number
            return v < limit
        return validator

    fecha_emision = Property(fecha_emision_validator)
    ruc = Property()
    establecimiento = Property()
    punto_emision = Property()
    numero = Property(max_digits_validator(9))
    codigo = Property(max_digits_validator(8))

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
                  "{:03d}".format(self.establecimiento) +
                  "{:03d}".format(self.punto_emision) +
                  "{:09d}".format(self.numero) +
                  "{:08d}".format(self.codigo) +
                  self.tipo_emision.code)

        res = codigo + self.comprobante(codigo)
        return res


###########################
# Items
##########################
class BillItem(models.Model):
    """
    Base class for items that are part of a bill
    """
    qty = models.DecimalField(max_digits=10, decimal_places=4)
    sku = models.ForeignKey(SKU)
    discount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    bill = models.ForeignKey(Bill)

    def save(self, **kwargs):
        if self.bill.can_be_modified:
            super(BillItem, self).save(**kwargs)
        else:
            raise ValidationError("No se puede modificar la factura")

    def delete(self, **kwargs):
        if self.bill.can_be_modified:
            super(BillItem, self).delete(**kwargs)
        else:
            raise ValidationError("No se puede modificar la factura")

    @property
    def unit_cost(self):
        return self.sku.batch.unit_cost

    @property
    def margin_percent(self):
        return ((self.unit_price/self.unit_cost) - 1) * 100

    @property
    def max_discount(self):
        return (self.unit_price - self.unit_cost) * self.qty

    @property
    def base_unit_price(self):
        return self.sku.unit_price

    @property
    def unit_price(self):
        return self.sku.unit_price

    @property
    def iva(self):
        return self.sku.batch.item.iva

    @property
    def ice(self):
        return self.sku.batch.item.ice

    @property
    def base_total_sin_impuestos(self):
        return (self.qty * self.unit_price)

    @property
    def total_sin_impuestos(self):
        return (self.qty * self.unit_price) - self.discount

    @property
    def valor_ice(self):
        if self.ice:
            return (self.total_sin_impuestos *
                    (self.ice.porcentaje / Decimal("100.0")))
        else:
            return Decimal(0)

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

    @property
    def increment_qty(self):
        return self.sku.batch.item.increment_qty

    @property
    def name(self):
        return self.sku.batch.item.name

    @property
    def code(self):
        return self.sku.code

    @property
    def decimales_qty(self):
        return self.sku.decimales_qty

    def substract_from_inventory(self):
        self.sku.substract(self.qty)


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
    porcentaje = models.DecimalField(max_digits=5, decimal_places=2)
    forma_pago = models.ForeignKey(FormaPago)
    plazo_pago = models.ForeignKey(PlazoPago)
    bill = models.ForeignKey(Bill)

    @property
    def cantidad(self):
        return ((self.porcentaje * self.bill.total_con_impuestos)
                / Decimal(100))

    @property
    def date(self):
        return self.bill.date.date() + timedelta(days=self.plazo_pago.tiempo)

    def save(self, **kwargs):
        if self.bill.can_be_modified:
            super(Pago, self).save(**kwargs)
        else:
            raise ValidationError("No se puede modificar la factura")

    def delete(self, **kwargs):
        if self.bill.can_be_modified:
            super(Pago, self).delete(**kwargs)
        else:
            raise ValidationError("No se puede modificar la factura")
