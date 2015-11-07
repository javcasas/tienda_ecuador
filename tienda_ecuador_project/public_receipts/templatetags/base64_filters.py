from django import template
import base64

register = template.Library()

@register.filter
def base64_encode(value):
    return base64.b64encode(value)

@register.filter
def base64_decode(value):
    return base64.b64decode(value)
