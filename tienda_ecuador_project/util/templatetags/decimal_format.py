from django import template
from decimal import Decimal

register = template.Library()


def exn_to_str(fn):
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
        return ("The type of '{}' is {}, not {}".format(
                value, type(value), Decimal))

    if type(arg) is not int:
        raise Exception("The type of '{}' is {}, not {}".format(
                        arg, type(arg), int))

    format_string = "{{:.{}f}}".format(arg)
    return format_string.format(value)


@register.filter
def decimals2(value):
    """
    Formats with 2 decimal digits
    """
    return decimals(value, 2)

@register.filter
def decimals4(value):
    """
    Formats with 4 decimal digits
    """
    return decimals(value, 4)


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
def qty(ob):
    """
    Quantity with no digits (integer) or 4 digits (non-integer)
    """
    decimales = ob.decimales_qty
    return decimals(ob.qty, decimales)
