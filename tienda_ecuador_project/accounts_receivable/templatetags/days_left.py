import functools
from django import template
from decimal import Decimal

register = template.Library()

def exn_to_str(fn):
    #@functools.wraps(fn)
    def wrapped_fn(*args):
        try:
            return fn(*args)
        except Exception as e:
            return str(e)
    return wrapped_fn

@register.filter(name='days_left_to_css_class')
def days_left_to_css_class(value):
    """
    """
    if value < 3:
        return "danger text-danger"
    elif value < 6:
        return "warning text-warning"
    else:
        return ""
