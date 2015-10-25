# * encoding: utf8 *
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE',
                      'tienda_ecuador_project.settings')

import django
django.setup()

from functools import partial
from datetime import datetime
import pytz
from billing.models import (Item, ProformaBill, ProformaBillItem,
                            Customer, Iva, Ice)
from billing import models
import company_accounts.models
from django.contrib.auth.models import User


def get_date():
    return datetime.now(tz=pytz.timezone('America/Guayaquil'))


def print_instance(klass, kwargs):
    params = u", ".join([u"{}={}".format(k, v)
                        for (k, v) in kwargs.iteritems()])
    print u"Adding", klass.__name__, params


def add_instance(klass, **kwargs):
    print_instance(klass, kwargs)
    s = klass.objects.update_or_create(**kwargs)[0]
    s.full_clean()
    s.save()
    return s

add_Company = partial(add_instance, company_accounts.models.Company)
add_Item = partial(add_instance, Item)
add_Customer = partial(add_instance, Customer)
add_CompanyUser = partial(add_instance, company_accounts.models.CompanyUser)
add_ProformaBill = partial(add_instance, ProformaBill)
add_ProformaBillItem = partial(add_instance, ProformaBillItem)


def add_User(**kwargs):
    u = add_instance(User, **kwargs)
    u.set_password(kwargs['password'])
    u.save()
    return u


def my_populate():
    u1, created = User.objects.get_or_create(username='javier')
    u1.set_password("tiaputa")
    u1.is_staff = True
    u1.is_superuser = True
    u1.save()


    t1 = add_Company(nombre_comercial=u"DSSTI", ruc=u'1756760292001',
                     razon_social=u'CASAS VELASCO JAVIER',
                     direccion_matriz=u'C/ Francisco de Orellana Oe2-143, Tumbaco, Quito')
    e1 = add_instance(company_accounts.models.Establecimiento,
                      company=t1,
                      direccion=t1.direccion_matriz,
                      descripcion='Matriz',
                      codigo='001')
    pe1 = add_instance(company_accounts.models.PuntoEmision,
                       establecimiento=e1,
                       descripcion='Caja principal',
                       codigo='001')

    u2, created = User.objects.get_or_create(username='test')
    u2.set_password("test")
    u2.save()

    return locals()


if __name__ == '__main__':
    print "Starting Billing population script..."
    my_populate()
