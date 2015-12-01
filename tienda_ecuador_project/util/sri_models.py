# * encoding: utf-8 *
from django.db import models
from django.core.exceptions import ValidationError


class SRIStatus(object):
    class options(object):
        NotSent = 'NotSent'
        ReadyToSend = 'ReadyToSend'
        Sent = 'Sent'
        Accepted = 'Accepted'

    @classmethod
    def pretty_print(cls, ob):
        return dict(SRIStatus.__OPTIONS__)[ob]

    __OPTIONS__ = (
        ('NotSent', 'No enviado al SRI'),
            # Invalido o no enviado
        ('ReadyToSend', 'Enviando al SRI'),
            # Tiene fecha y punto de emision
            # al enviar se genera XML, clave de acceso y se incrementan secuenciales
        ('Sent', 'Enviada al SRI'),
        ('Accepted', 'Aceptada por el SRI'),
    )


class AmbienteSRI(object):
    class options(object):
        pruebas = 'pruebas'
        produccion = 'produccion'

    @classmethod
    def pretty_print(cls, ob):
        return dict(cls.__OPTIONS__)[ob]

    __OPTIONS__ = (
        ('pruebas', 'Pruebas'),
        ('produccion', 'Producción')
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

    @property
    def can_be_modified(self):
        if not self.id:
            # Not saved yet
            return True
        prev = self.__class__.objects.get(id=self.id)
        return prev.status == SRIStatus.options.NotSent

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
