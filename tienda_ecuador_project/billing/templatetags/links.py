from django import template
from django.core.urlresolvers import reverse

register = template.Library()


def wrap_btn_group(text):
    return """
<div class='btn-group'>
    {}
</div>
""".format(text)


@register.simple_tag()
def button(text, view, *view_params):
    """
    Formats with arg decimal digits
    """
    html = wrap_btn_group("<a href='{url}' class='btn btn-default'>{text}</a>")
    url = reverse(view, args=view_params)
    return html.format(url=url, text=text)


@register.simple_tag()
def primary_button(text, view, *view_params):
    """
    Formats with arg decimal digits
    """
    html = wrap_btn_group("<a href='{url}' class='btn btn-primary'>{text}</a>")
    url = reverse(view, args=view_params)
    return html.format(url=url, text=text)


@register.simple_tag()
def danger_button(text, view, *view_params):
    """
    """
    html = wrap_btn_group("<a href='{url}' class='btn btn-danger'>{text}</a>")
    url = reverse(view, args=view_params)
    return html.format(url=url, text=text)


@register.simple_tag()
def back_button(view, *view_params):
    return button("Volver", view, *view_params)


@register.simple_tag()
def edit_button(view, *view_params):
    return primary_button("Editar", view, *view_params)


@register.simple_tag()
def save_button():
    return wrap_btn_group("<button type='submit' class='btn btn-primary'>Guardar</button>")


@register.simple_tag()
def dont_save_button(view, *view_params):
    return button("No Guardar", view, *view_params)


@register.simple_tag()
def delete_button():
    return wrap_btn_group("<button type='submit' class='btn btn-danger'>Eliminar</button>")


@register.simple_tag()
def dont_delete_button(view, *view_params):
    return button("No Eliminar", view, *view_params)


@register.tag(name='buttons_menu')
def do_button_menu(parser, token):
    nodelist = parser.parse(('endbuttons_menu',))
    parser.delete_first_token()
    return ButtonMenuNode(nodelist)


class ButtonMenuNode(template.Node):
    def __init__(self, nodelist):
        self.nodelist = nodelist

    def render(self, context):
        output = self.nodelist.render(context)
        output = """
<div class='btn-group-justified'>
{}
</div>
""".format(output)
        return output
