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
    u1 = add_User(username='roberto', password='qwerty', email='')
    u2 = add_User(username='luis', password='qwerty', email='')
    u3, created = User.objects.get_or_create(username='javier')
    u3.set_password("tiaputa")
    u3.is_staff = True
    u3.is_superuser = True
    u3.save()

    u4, created = User.objects.get_or_create(username='test')
    u4.set_password("test")
    u4.save()

    t1 = add_Company(nombre_comercial=u"Electro Tienda", ruc=u'1234567890',
                     razon_social=u'Roberto Gutiérrez', direccion_matriz=u'C/ Rumiñahui')
    t2 = add_Company(nombre_comercial=u"Mega Iluminación", ruc=u'1234567891',
                     razon_social=u'Alberto Álvarez', direccion_matriz=u'C/ Orellana')
    e1 = add_instance(company_accounts.models.Establecimiento,
                      company=t1,
                      direccion='C/ Ruminahui',
                      descripcion='Matriz',
                      codigo='001')
    e2 = add_instance(company_accounts.models.Establecimiento,
                      company=t2,
                      direccion='C/ Orellana',
                      descripcion='Matriz',
                      codigo='001')
    pe1 = add_instance(company_accounts.models.PuntoEmision,
                       establecimiento=e1,
                       descripcion='Caja principal',
                       codigo='001')
    pe2 = add_instance(company_accounts.models.PuntoEmision,
                       establecimiento=e2,
                       descripcion='Caja principal',
                       codigo='001')

    iva, created = Iva.objects.get_or_create(descripcion="12%", porcentaje=12)
    ice, created = Ice.objects.get_or_create(descripcion="Bebidas gaseosas.", porcentaje=50, grupo=1)
    i11 = add_Item(sku='115674', name='Foco LED Blanco 5W',
                   unit_cost=10, unit_price=17, tipo='producto',
                   description='Foco LED, luz blanca, potencia: 5W', company=t1,)
    i12 = add_Item(sku='120443', name='Foco LED Amarillo 6W',
                   unit_cost=8, unit_price=11, tipo='producto',
                   description='Foco LED, luz amarilla, potencia: 6W', company=t1)
    i21 = add_Item(sku='F114', name='Panel LED Blanco 50W',
                   unit_cost=30, unit_price=45, tipo='producto',
                   description='Panel de LED, de luz blanca, 50W', company=t2)
    i22 = add_Item(sku='F116', name='Panel LED RGB 35W',
                   unit_cost=33, unit_price=54, tipo='producto',
                   description='Panel de LED RGB, de 35W', company=t2)
    i23 = add_Item(sku='F117', name='Foco LED verde 4W',
                   unit_cost=20, unit_price=27, tipo='producto',
                   description='Foco LED verde decorativo, 4W', company=t2)
    for i in [i11, i12, i21, i22, i23]:
        i.tax_items.add(iva, ice)

    c1 = add_Customer(razon_social=u'Alberto Gómez', tipo_identificacion='cedula',
                      identificacion="1756760292", email='alberto.gomez@yahoo.com',
                      company=t1)
    c2 = add_Customer(razon_social=u'Román Correa', tipo_identificacion='ruc',
                      identificacion="1756760292001", company=t1)
    c3 = add_Customer(razon_social=u'María del Mar Orellana', tipo_identificacion='ruc',
                      identificacion="1756760219001", company=t2)

    ut1 = add_CompanyUser(user=u1, company=t1)
    ut2 = add_CompanyUser(user=u2, company=t2)
    ut3 = add_CompanyUser(user=u3, company=t1)
    ut4 = add_CompanyUser(user=u4, company=t1)

    b1 = add_ProformaBill(issued_to=c1, number='145',
                          punto_emision=pe1,
                          date=get_date())
    b1i1 = add_ProformaBillItem(
        sku='115674', name='Foco LED Blanco 5W',
        unit_cost=10, unit_price=17, tipo='producto',
        description='Foco LED, luz blanca, potencia: 5W',
        proforma_bill=b1, qty=4)
    b1i2 = add_ProformaBillItem(
        sku='120443', name='Foco LED Amarillo 6W',
        unit_cost=8, unit_price=11, tipo='producto',
        description='Foco LED, luz amarilla, potencia: 6W',
        proforma_bill=b1, qty=8)

    b2 = add_ProformaBill(issued_to=c1, number='1453',
                          date=get_date(),
                          punto_emision=pe1)
    b2i1 = add_ProformaBillItem(
        sku='115674', name='Foco LED Blanco 5W',
        unit_cost=10, unit_price=17, tipo='producto',
        description='Foco LED, luz blanca, potencia: 5W',
        proforma_bill=b2, qty=9)
    b2i2 = add_ProformaBillItem(
        sku='120443', name='Foco LED Amarillo 6W',
        unit_cost=8, unit_price=11, tipo='producto',
        description='Foco LED, luz amarilla, potencia: 6W',
        proforma_bill=b2, qty=11)

    b3 = add_ProformaBill(issued_to=c3, number='1453',
                          date=get_date(),
                          punto_emision=pe2)
    for i in [b1i1, b1i2, b2i1, b2i2]:
        i.tax_items.add(iva, ice)
    return locals()


if __name__ == '__main__':
    print "Starting Billing population script..."
    my_populate()
