from django import template
from django.core.urlresolvers import reverse
from django.utils.safestring import mark_safe

register = template.Library()




class Button(object):
    def __init__(self, name, view=None, view_args=None, btn_class='default', btn_extra_classes=None, btn_type='a', wrap_btn_group=False):
        self.name = name
        self.view = view
        self.btn_class = btn_class
        self.btn_extra_classes = btn_extra_classes or []
        self.btn_type = btn_type
        self.wrap_btn_group = wrap_btn_group
        self.view = view
        self.view_args = view_args

    def __html__(self):
        css_class = 'btn btn-{btn_class}'.format(btn_class=self.btn_class)
        for extra_class in self.btn_extra_classes:
            css_class += " " + extra_class

        if self.btn_type == 'a':
            template = u"<a href='{url}' class='{css_class}'>{name}</a>"
            url = reverse(self.view, args=self.view_args)
        elif self.btn_type == 'button':
            template = u"<button type='submit' class='{css_class}'>{name}</a>"
            url = None
        else:
            raise Exception("Unknown button type: {}".format(self.btn_type))

        if self.wrap_btn_group:
            template = u"""<div class='btn-group'> {} </div>""".format(template)

        res = template.format(url=url, css_class=css_class, name=self.name)
        return mark_safe(res)



@register.simple_tag()
def button(name, view, *view_params):
    return Button(name, view=view, view_args=view_params)


@register.simple_tag()
def fullwidth_button(name, view, *view_params):
    return Button(name, view=view, view_args=view_params,
                  btn_extra_classes=['btn-block'])


@register.simple_tag()
def fullwidth_primary_button(name, view, *view_params):
    return Button(name, view=view, view_args=view_params,
                  btn_class='primary',
                  btn_extra_classes=['btn-block'])


@register.simple_tag()
def primary_button(name, view, *view_params):
    return Button(name, view=view, view_args=view_params,
                  btn_class='primary')


@register.simple_tag()
def danger_button(text, view, *view_params):
    return Button(name, view=view, view_args=view_params,
                  btn_class='danger')


@register.simple_tag()
def back_button(view, *view_params):
    return Button('Volver', view=view, view_args=view_params)


@register.simple_tag()
def edit_button(view, *view_params):
    return Button('Editar', view=view, view_args=view_params,
                  btn_class='primary')


@register.simple_tag()
def save_button():
    return Button('Guardar', btn_type='button', btn_class='primary', wrap_btn_group=True)


@register.simple_tag()
def dont_save_button(view, *view_params):
    return Button("No Guardar", view=view, view_args=view_params)


@register.simple_tag()
def delete_button():
    return Button('Eliminar', btn_type='button', btn_class='danger', wrap_btn_group=True)


@register.simple_tag()
def dont_delete_button(view, *view_params):
    return button("No Eliminar", view, *view_params)



@register.simple_tag()
def main_menu_button(name, view, *view_params):
    return Button(name, view=view, view_args=view_params,
                  btn_extra_classes=['btn-lg', 'col-xs-12', 'col-sm-6', 'col-lg-4'])


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
        output = u"""
<div class='btn-group-justified'>
{}
</div>
""".format(output)
        return output
