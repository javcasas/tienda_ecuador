# * encoding: utf-8 *
from datetime import datetime, timedelta
import json
import pytz
from decimal import Decimal

from django.db import models
from django.core.exceptions import ValidationError
from django.db import transaction

from util import sri_sender
from util.enum import Enum


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
    def __nonzero__(self):
        return self.descripcion != "No ICE"

    def __unicode__(self):
        return u"{:.0f}% - {}".format(self.porcentaje, self.descripcion)


SRIStatus = Enum(
    "SRIStatus",
    (   # Invalido o no enviado
        ('NotSent', 'No enviado al SRI'),

        # Tiene fecha y punto de emision
        # Al enviar se genera XML, clave de acceso
        #     y se incrementan secuenciales
        ('ReadyToSend', 'Enviando al SRI'),
        # Enviada al SRI, esperando aceptacion o rechazo
        ('Sent', 'Enviada al SRI'),
        # Aceptada por el SRI
        ('Accepted', 'Aceptada por el SRI'),
        # Rechazada por el SRI, puede volver a ser modificada y enviada
        ('Rejected', 'Rechazada por el SRI'),

        # Estaba aceptado por el SRI y fue anulado
        ('Annulled', 'Anulado'),
    )
)


AmbienteSRI = Enum(
    "AmbienteSRI",
    (
        ('pruebas', 'Pruebas'),
        ('produccion', 'Producción')
    )
)


class ComprobanteSRIMixin(models.Model):
    """
    Mixin that checks if the bill can be modified before saving it
    """
    class Meta:
        abstract = True

    xml_content = models.TextField(blank=True)

    clave_acceso = models.CharField(
        max_length=50, blank=True, default='')
    numero_autorizacion = models.CharField(
        max_length=50, blank=True, default='')
    fecha_autorizacion = models.DateTimeField(
        null=True, blank=True)
    issues = models.TextField(
        default='', blank=True)

    ambiente_sri = models.CharField(
        max_length=20,
        choices=AmbienteSRI.__OPTIONS__)

    status = models.CharField(
        max_length=20,
        choices=SRIStatus.__OPTIONS__,
        default=SRIStatus.options.NotSent)

    sri_last_check = models.DateTimeField(
        null=True, blank=True)

    @property
    def can_be_modified(self):
        if not self.id:
            # Not saved yet
            return True
        prev = self.__class__.objects.get(id=self.id)
        return prev.status in [SRIStatus.options.NotSent, SRIStatus.options.Rejected]

    def save(self, **kwargs):
        """
        Checks if the bill can be modified, based on the status
        """
        if self.can_be_modified:
            if self.punto_emision:
                try:
                    self.company
                except:
                    self.company = self.punto_emision.establecimiento.company
                if not self.ambiente_sri:
                    self.ambiente_sri = self.punto_emision.ambiente_sri
            if self.status == SRIStatus.options.ReadyToSend:
                errors = []
                if not self.punto_emision:
                    errors.append("No hay punto de emision")
                if not self.date:
                    errors.append("No hay fecha de emision")
                if errors:
                    raise ValidationError(". ".join(errors))
            return super(ComprobanteSRIMixin, self).save(**kwargs)
        else:
            raise ValidationError("No se puede modificar el comprobante")

    def secret_save(self, **kwargs):
        """
        Always saves, ignoring checks
        """
        return super(ComprobanteSRIMixin, self).save(**kwargs)

    def delete(self, **kwargs):
        """
        Checks if the bill can be modified, based on the status
        """
        if self.can_be_modified:
            return super(ComprobanteSRIMixin, self).delete(**kwargs)
        else:
            raise ValidationError("No se puede modificar el comprobante")

    def secret_delete(self, **kwargs):
        """
        Always saves, ignoring checks
        """
        return super(ComprobanteSRIMixin, self).save(**kwargs)

    # SRI-related operations
    def accept(self):
        """
        Marks a bill as ReadyToSend
        """
        assert self.status in [SRIStatus.options.NotSent, SRIStatus.options.Rejected]
        assert self.ambiente_sri in [AmbienteSRI.options.pruebas,
                                     AmbienteSRI.options.produccion]
        self.status = SRIStatus.options.ReadyToSend
        self.save()

    def send_to_SRI(self):
        """
        Sends a bill to SRI
        Requires:
            XML
            Clave Acceso
            status = ReadyToSend
            ambiente_sri
            punto_emision
        After:
            status = Sent or NotSent
            maybe Issues
        """
        assert self.status == SRIStatus.options.ReadyToSend
        assert self.ambiente_sri in [AmbienteSRI.options.pruebas,
                                     AmbienteSRI.options.produccion]
        assert self.punto_emision

        def convert_messages(messages):
            def convert_msg(msg):
                converted = {}
                for key in ['tipo', 'identificador',
                            'mensaje', 'informacionAdicional']:
                    converted[key] = getattr(msg, key, None)
                return converted
            return [convert_msg(msg) for msg in messages]

        # Check it has not been sent and accepted
        autorizar_comprobante_result = sri_sender.autorizar_comprobante(
            self.clave_acceso, entorno=self.ambiente_sri)
        if int(autorizar_comprobante_result.numeroComprobantes) > 0:
            for autorizacion in autorizar_comprobante_result.autorizaciones.autorizacion:
                if autorizacion.estado == 'AUTORIZADO':
                    self.status = SRIStatus.options.Sent
                    self.secret_save()
                    return True
                elif autorizacion.estado == 'RECHAZADA':
                    pass
                else:  # Not processed yet
                    return False

        with transaction.atomic():
            punto_emision = self.punto_emision

            self.ambiente_sri = punto_emision.ambiente_sri
            self.secuencial = {
                'pruebas': punto_emision.siguiente_secuencial_pruebas,
                'produccion': punto_emision.siguiente_secuencial_produccion,
            }[self.ambiente_sri]
            self.secret_save()

            # Generate and sign XML
            xml_data, clave_acceso = self.gen_xml()

            self.xml_content = xml_data
            self.clave_acceso = clave_acceso
            self.issues = ''
            self.secret_save()

            enviar_comprobante_result = sri_sender.enviar_comprobante(
                self.xml_content, entorno=self.ambiente_sri)
            if enviar_comprobante_result.estado == 'RECIBIDA':
                punto_emision = self.punto_emision
                if self.ambiente_sri == AmbienteSRI.options.pruebas:
                    punto_emision.siguiente_secuencial_pruebas += 1
                else:
                    punto_emision.siguiente_secuencial_produccion += 1
                punto_emision.save()
                self.status = SRIStatus.options.Sent
                self.secret_save()
                res = True
            else:
                enviar_msgs = (enviar_comprobante_result.comprobantes
                               .comprobante[0].mensajes.mensaje)
                self.issues = json.dumps(convert_messages(enviar_msgs))
                self.status = SRIStatus.options.Rejected
                self.secret_save()
                res = False
        assert self.status in [SRIStatus.options.Sent,
                               SRIStatus.options.Rejected]
        return res

    def validate_in_SRI(self):
        """
        Validates a bill in SRI
        Requires:
            Clave Acceso
            status = Sent
            ambiente_sri
        After:
            1: Being processed
                status = Sent
                Nothing changed
            2: Accepted
                status = Accepted
                Fecha autorizacion
                numero autorizacion
                maybe Issues
            3: Rejected
                status = NotSent
                Fecha autorizacion
                Issues
            sri_last_check is set to now
        """
        assert self.clave_acceso
        assert self.status == SRIStatus.options.Sent
        assert self.ambiente_sri in [AmbienteSRI.options.pruebas,
                                     AmbienteSRI.options.produccion]

        def convert_messages(messages):
            def convert_msg(msg):
                converted = {}
                for key in ['tipo', 'identificador',
                            'mensaje', 'informacionAdicional']:
                    converted[key] = getattr(msg, key, None)
            return map(convert_msg, messages)

        autorizar_comprobante_result = sri_sender.autorizar_comprobante(
            self.clave_acceso, entorno=self.ambiente_sri)

        if int(autorizar_comprobante_result.numeroComprobantes) > 0:
            already_authorised = False
            for autorizacion in autorizar_comprobante_result.autorizaciones.autorizacion:
                # This should not happen, but it happened
                # The same bill was submitted twice, with same everything but randoms from signature
                # It was approved both times
                if autorizacion.estado == 'AUTORIZADO':
                    if already_authorised:
                        self.company.add_db_issue("""
El comprobante con clave de acceso {clave_acceso} ha sido enviado y aprobado dos veces, con
códigos de autorización {cod_1} y {cod_2}. Se recomienda anular el segundo."""
                            .format(clave_acceso=autorizar_comprobante_result.claveAccesoConsultada,
                                    cod_1=self.numero_autorizacion,
                                    cod_2=autorizacion.numeroAutorizacion))
                    else:
                        self.fecha_autorizacion = autorizacion.fechaAutorizacion
                        self.numero_autorizacion = autorizacion.numeroAutorizacion
                        if autorizacion.mensajes:
                            self.issues = json.dumps(
                                convert_messages(autorizacion.mensajes.mensaje))
                        self.status = SRIStatus.options.Accepted
                        self.secret_save()
                        res = True
                        already_authorised = True
                elif autorizacion.estado == 'RECHAZADA':
                    self.fecha_autorizacion = autorizacion.fechaAutorizacion
                    self.issues = json.dumps(
                        convert_messages(autorizacion.mensajes.mensaje))
                    self.status = SRIStatus.options.Rejected
                    self.secret_save()
                    res = False
                else:  # Aun no procesado??
                    # FIXME: log
                    res = False
        else:
            res = False

        self.sri_last_check = datetime.now(
            tz=pytz.timezone('America/Guayaquil'))

        self.secret_save()

        if self.status == SRIStatus.options.Sent:
            # Nothing changed
            pass
        elif self.status == SRIStatus.options.Accepted:
            assert self.fecha_autorizacion
            assert self.numero_autorizacion
        elif self.status == SRIStatus.options.Rejected:
            assert self.fecha_autorizacion
            assert self.issues
        else:
            assert False  # This should not happen
        return res

    def check_if_annulled_worthy(self):
        if self.status != SRIStatus.options.Accepted:
            return False
        if datetime.now(tz=pytz.timezone('America/Guayaquil')) - self.fecha_autorizacion < timedelta(days=15):
            if not self.sri_last_check:
                return True
            elif datetime.now(tz=pytz.timezone('America/Guayaquil')) - self.sri_last_check > timedelta(hours=1):
                return True
        return False

    def check_if_annulled_in_SRI(self):
        """
        Checks if a bill has been annulled in SRI
        Requires:
            Clave Acceso
            status = Accepted
            ambiente_sri
            fecha_autorizacion is no more than 15 days old
        After:
            1: No
                status = Accepted
            2: Yes
                status = Annulled
            sri_last_check is set to now
        """
        assert self.clave_acceso
        assert self.status == SRIStatus.options.Accepted
        assert self.ambiente_sri in [AmbienteSRI.options.pruebas,
                                     AmbienteSRI.options.produccion]
        assert datetime.now(tz=pytz.timezone('America/Guayaquil')) - self.fecha_autorizacion < timedelta(days=15)

        autorizar_comprobante_result = sri_sender.autorizar_comprobante(
            self.clave_acceso, entorno=self.ambiente_sri)

        if int(autorizar_comprobante_result.numeroComprobantes) == 1:
            # All right
            res = False
        elif int(autorizar_comprobante_result.numeroComprobantes) == 0:
            self.status = SRIStatus.options.Annulled
            res = True

        self.sri_last_check = datetime.now(tz=pytz.timezone('America/Guayaquil'))
        self.secret_save()
        return res
