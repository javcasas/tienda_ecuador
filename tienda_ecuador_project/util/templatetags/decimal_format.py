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

@register.filter(name='decimals')
def decimals(value, arg):
    """
    Formats with arg decimal digits
    """
    if type(value) is not Decimal:
        #raise Exception("The type of '{}' is {}, not {}".format(value, type(value), Decimal)) 
        return ("The type of '{}' is {}, not {}".format(value, type(value), Decimal)) 
        
    if type(arg) is not int:
        raise Exception("The type of '{}' is {}, not {}".format(arg, type(arg), int)) 

    format_string = "{{:.{}f}}".format(arg)
    return format_string.format(value)


@register.filter
def price2d(value):
    """
    Price with two decimals
    """
    return "$" + decimals(value, 2)


@register.filter
def money_2d(value):
    """
    Price with two decimals
    """
    return "$" + decimals(value, 2)

@register.filter
def money_4d(value):
    """
    Price with two decimals
    """
    return "$" + decimals(value, 4)

@register.filter
def price4d(value):
    """
    Price with four decimals
    """
    return "$" + decimals(value, 4)

@register.filter
def qty(value):
    """
    Quantity with no digits (integer) or 4 digits (non-integer)
    """
    if value.to_integral_value() == value:
        # Is an integer
        return decimals(value, 0)
    else:
        # Not an integer
        return decimals(value, 4)
