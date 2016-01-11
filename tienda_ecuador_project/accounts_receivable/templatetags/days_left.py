from django import template

register = template.Library()


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
