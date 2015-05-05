import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tienda_ecuador_project.settings')

import django
django.setup()

from billing.models import Shop, Item, Bill, BillItem, Customer, Shop, ShopUser
from django.contrib.auth.models import User
from functools import partial


def add_instance(klass, **kwargs):
    print "Adding", klass.__name__, ", ".join(["{}={}".format(k, v) for (k, v) in kwargs.iteritems()])
    s = klass.objects.get_or_create(**kwargs)[0]
    s.save()
    return s

add_shop = partial(add_instance, Shop)
add_item = partial(add_instance, Item)
add_customer = partial(add_instance, Customer)
add_shop_user = partial(add_instance, ShopUser)
add_bill = partial(add_instance, Bill)
add_bill_item = partial(add_instance, BillItem)


def add_user(**kwargs):
    pw = kwargs.pop("password")
    u = add_instance(User, **kwargs)
    u.set_password(pw)
    u.save()
    return u

def my_populate():
    t1 = add_shop(name="Tienda 1")
    t2 = add_shop(name="Tienda 2")

    i11 = add_item(sku='t1-123', name='Item T11', description='Item 1 en Tienda 1', shop=t1)
    i12 = add_item(sku='t1-146', name='Item T12', description='Item 2 en Tienda 1', shop=t1)
    i21 = add_item(sku='t2-723', name='Item T21', description='Item 1 en Tienda 2', shop=t2)
    i22 = add_item(sku='t2-946', name='Item T22', description='Item 2 en Tienda 2', shop=t2)
    i23 = add_item(sku='t2-146', name='Item T23', description='Item 3 en Tienda 2', shop=t2)

    c1 = add_customer(name='Paco')
    c2 = add_customer(name='Pepe')
    c3 = add_customer(name='Luis')

    u1 = add_user(username='roberto', password='qwerty', email='')
    ut1 = add_shop_user(user=u1, shop=t1)
    u2 = add_user(username='luis', password='qwerty', email='')
    ut2 = add_shop_user(user=u2, shop=t2)
    ut3 = add_shop_user(user=User.objects.get(username='javier'), shop=t1)

    b1 = add_bill(issued_to=c1, number='145', shop=t1, is_proforma=True)
    b1i1 = add_bill_item(sku='t1-123', name='Item T11', description='Item 1 en Tienda 1', shop=t1, bill=b1, qty=4)
    b1i1 = add_bill_item(sku='t1-146', name='Item T12', description='Item 2 en Tienda 1', shop=t1, bill=b1, qty=8)

    b2 = add_bill(issued_to=c1, number='1453', shop=t1, is_proforma=False)
    b2i1 = add_bill_item(sku='t1-123', name='Item T11', description='Item 1 en Tienda 1', shop=t1, bill=b2, qty=4)
    b2i1 = add_bill_item(sku='t1-146', name='Item T12', description='Item 2 en Tienda 1', shop=t1, bill=b2, qty=8)
    

if __name__ == '__main__':
    print "Starting Billing population script..."
    my_populate()
