from django import template
from decimal import Decimal

register = template.Library()

@register.filter
def decimals(value, arg):
    """
    Formats with arg decimal digits
    """
    if type(value) is not Decimal:
        raise Exception("The type of '{}' is {}, not {}".format(value, type(value), Decimal)) 
        
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
def price4d(value):
    """
    Price with four decimals
    """
    return "$" + decimals(value, 4)
