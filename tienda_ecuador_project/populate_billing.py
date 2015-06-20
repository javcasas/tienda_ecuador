import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tienda_ecuador_project.settings')

import django
django.setup()

from billing.models import Company, Item, ProformaBill, ProformaBillItem, CompanyUser, Customer, Iva, Ice
from django.contrib.auth.models import User
from functools import partial
from datetime import datetime
import pytz

def get_date():
    return datetime.now(tz=pytz.timezone('America/Guayaquil'))

def print_instance(klass, kwargs):
    print "Adding", klass.__name__, ", ".join(["{}={}".format(k, v) for (k, v) in kwargs.iteritems()])

def add_instance(klass, **kwargs):
    print_instance(klass, kwargs)
    s = klass.objects.update_or_create(**kwargs)[0]
    s.save()
    return s

add_Company = partial(add_instance, Company)
add_Item = partial(add_instance, Item)
add_Customer = partial(add_instance, Customer)
add_CompanyUser = partial(add_instance, CompanyUser)
add_ProformaBill = partial(add_instance, ProformaBill)
add_ProformaBillItem = partial(add_instance, ProformaBillItem)


def add_User(**kwargs):
    pw = kwargs.pop("password")
    u = add_instance(User, **kwargs)
    u.set_password(pw)
    u.save()
    return u

def my_populate():
    u3, created = User.objects.get_or_create(username='javier')
    u3.set_password("tiaputa")
    u3.is_staff = True
    u3.is_superuser = True
    u3.save()

    t1 = add_Company(nombre_comercial="Tienda 1", ruc='1234567890',
                     razon_social='Tienda1', direccion_matriz='C del pipino')
    t2 = add_Company(nombre_comercial="Tienda 2", ruc='1234567891',
                     razon_social='Tienda2', direccion_matriz='C del nabo')

    iva = add_instance(Iva, descripcion="12%", codigo="2", porcentaje=12.0)
    ice = add_instance(Ice, descripcion="Bebidas gaseosas", grupo=1, codigo="3051", porcentaje=50.0)
    i11 = add_Item(sku='t1-123', name='Item T11',
                   iva=iva, ice=ice, unit_cost=10, unit_price=17,
                   description='Item 1 en Tienda 1', company=t1)
    i12 = add_Item(sku='t1-146', name='Item T12',
                   iva=iva, ice=ice, unit_cost=1, unit_price=3,
                   description='Item 2 en Tienda 1', company=t1)
    i21 = add_Item(sku='t2-723', name='Item T21',
                   iva=iva, ice=ice, unit_cost=10, unit_price=17,
                   description='Item 1 en Tienda 2', company=t2)
    i22 = add_Item(sku='t2-946', name='Item T22',
                   iva=iva, ice=ice, unit_cost=33, unit_price=37,
                   description='Item 2 en Tienda 2', company=t2)
    i23 = add_Item(sku='t2-146', name='Item T23',
                   iva=iva, ice=ice, unit_cost=20, unit_price=27,
                   description='Item 3 en Tienda 2', company=t2)

    c1 = add_Customer(razon_social='Paco', tipo_identificacion='cedula',
                      identificacion='123456543', email='paco@paco.net',
                      company=t1)
    c2 = add_Customer(razon_social='Pepe', tipo_identificacion='ruc',
                      identificacion='123454232001', company=t1)
    c3 = add_Customer(razon_social='Luis', tipo_identificacion='ruc',
                      identificacion='444444444001', company=t2)

    u1 = add_User(username='roberto', password='qwerty', email='')
    ut1 = add_CompanyUser(user=u1, company=t1)
    u2 = add_User(username='luis', password='qwerty', email='')
    ut2 = add_CompanyUser(user=u2, company=t2)
    ut3 = add_CompanyUser(user=u3, company=t1)

    b1 = add_ProformaBill(issued_to=c1, number='145',
                          date=get_date(),
                          company=t1)
    b1i1 = add_ProformaBillItem(sku='t1-123', name='Item T11',
                                iva=iva, ice=ice, unit_cost=5.0, unit_price=6.0,
                                description='Item 1 en Tienda 1', proforma_bill=b1, qty=4)
    b1i1 = add_ProformaBillItem(sku='t1-146', name='Item T12',
                                iva=iva, ice=ice, unit_cost=9.0, unit_price=12.0,
                                description='Item 2 en Tienda 1', proforma_bill=b1, qty=8)

    b2 = add_ProformaBill(issued_to=c1, number='1453',
                          date=get_date(),
                          company=t1)
    b2i1 = add_ProformaBillItem(sku='t1-123', name='Item T11',
                                iva=iva, ice=ice, unit_cost=4.0, unit_price=8.0,
                                description='Item 1 en Tienda 1', proforma_bill=b2, qty=4)
    b2i1 = add_ProformaBillItem(sku='t1-146', name='Item T12',
                                iva=iva, ice=ice, unit_cost=9.0, unit_price=12.0,
                                description='Item 2 en Tienda 1', proforma_bill=b2, qty=8)
    b3 = add_ProformaBill(issued_to=c3, number='1453',
                          date=get_date(),
                          company=t2)
    return locals()
    

if __name__ == '__main__':
    print "Starting Billing population script..."
    my_populate()
