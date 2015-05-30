import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tienda_ecuador_project.settings')

import django
django.setup()

from billing.models import Company, Item, ProformaBill, ProformaBillItem, CompanyUser, Customer
from django.contrib.auth.models import User
from functools import partial
from datetime import datetime
import pytz

def get_date():
    return datetime.now(tz=pytz.timezone('America/Guayaquil'))


def add_instance(klass, **kwargs):
    print "Adding", klass.__name__, ", ".join(["{}={}".format(k, v) for (k, v) in kwargs.iteritems()])
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

    t1 = add_Company(name="Tienda 1", sri_ruc='1234567890', sri_razon_social='Tienda1')
    t2 = add_Company(name="Tienda 2", sri_ruc='1234567891', sri_razon_social='Tienda2')

    i11 = add_Item(sku='t1-123', name='Item T11',
                   vat_percent=12, unit_cost=10, unit_price=17,
                   description='Item 1 en Tienda 1', company=t1)
    i12 = add_Item(sku='t1-146', name='Item T12',
                   vat_percent=12, unit_cost=1, unit_price=3,
                   description='Item 2 en Tienda 1', company=t1)
    i21 = add_Item(sku='t2-723', name='Item T21',
                   vat_percent=0, unit_cost=10, unit_price=17,
                   description='Item 1 en Tienda 2', company=t2)
    i22 = add_Item(sku='t2-946', name='Item T22',
                   vat_percent=12, unit_cost=33, unit_price=37,
                   description='Item 2 en Tienda 2', company=t2)
    i23 = add_Item(sku='t2-146', name='Item T23',
                   vat_percent=0, unit_cost=20, unit_price=27,
                   description='Item 3 en Tienda 2', company=t2)

    c1 = add_Customer(name='Paco', company=t1)
    c2 = add_Customer(name='Pepe', company=t1)
    c3 = add_Customer(name='Luis', company=t2)

    u1 = add_User(username='roberto', password='qwerty', email='')
    ut1 = add_CompanyUser(user=u1, company=t1)
    u2 = add_User(username='luis', password='qwerty', email='')
    ut2 = add_CompanyUser(user=u2, company=t2)
    ut3 = add_CompanyUser(user=u3, company=t1)

    b1 = add_ProformaBill(issued_to=c1, number='145',
                          date=get_date(),
                          company=t1)
    b1i1 = add_ProformaBillItem(sku='t1-123', name='Item T11',
                                vat_percent=12, unit_cost=5.0, unit_price=6.0,
                                description='Item 1 en Tienda 1', proforma_bill=b1, qty=4)
    b1i1 = add_ProformaBillItem(sku='t1-146', name='Item T12',
                                vat_percent=12, unit_cost=9.0, unit_price=12.0,
                                description='Item 2 en Tienda 1', proforma_bill=b1, qty=8)

    b2 = add_ProformaBill(issued_to=c1, number='1453',
                          date=get_date(),
                          company=t1)
    b2i1 = add_ProformaBillItem(sku='t1-123', name='Item T11',
                                vat_percent=0, unit_cost=4.0, unit_price=8.0,
                                description='Item 1 en Tienda 1', proforma_bill=b2, qty=4)
    b2i1 = add_ProformaBillItem(sku='t1-146', name='Item T12',
                                vat_percent=12, unit_cost=9.0, unit_price=12.0,
                                description='Item 2 en Tienda 1', proforma_bill=b2, qty=8)
    

if __name__ == '__main__':
    print "Starting Billing population script..."
    my_populate()
