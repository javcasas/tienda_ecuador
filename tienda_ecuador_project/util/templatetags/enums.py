from django import template
from django.core.urlresolvers import reverse
from django.utils.safestring import mark_safe

from sri.models import SRIStatus, AmbienteSRI
from stakeholders.models import TipoIdentificacion

register = template.Library()


@register.filter
def sri_status(data):
    return SRIStatus.pretty_print(data)


@register.filter
def ambiente_sri(data):
    return AmbienteSRI.pretty_print(data)


@register.filter
def tipo_identificacion(data):
    return TipoIdentificacion.pretty_print(data)
