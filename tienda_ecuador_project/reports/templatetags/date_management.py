from django import template

register = template.Library()


@register.filter
def month_name(value):
    """
    Converts month number to name
    """
    names = {
        1: u"Enero",
        2: u"Febrero",
        3: u"Marzo",
        4: u"Abril",
        5: u"Mayo",
        6: u"Junio",
        7: u"Julio",
        8: u"Agosto",
        9: u"Septiembre",
        10: u"Octubre",
        11: u"Noviembre",
        12: u"Diciembre",
    }
    return names[int(value)]
