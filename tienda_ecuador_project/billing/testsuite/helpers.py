from functools import partial

from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist

from billing import models


def add_instance(klass, **kwargs):
    """
    Add a instance of the specified class with the specified arguments,
    and returns it after saving it
    """
    s = klass.objects.get_or_create(**kwargs)[0]
    return s


add_Company = partial(add_instance, models.Company)
add_CompanyUser = partial(add_instance, models.CompanyUser)

add_ProformaBill = partial(add_instance, models.ProformaBill)
add_Bill = partial(add_instance, models.Bill)

add_Item = partial(add_instance, models.Item)
add_ProformaBillItem = partial(add_instance, models.ProformaBillItem)
add_BillItem = partial(add_instance, models.BillItem)

add_Customer = partial(add_instance, models.Customer)
add_BillCustomer = partial(add_instance, models.BillCustomer)
add_ProformaBillCustomer = partial(add_instance, models.ProformaBillCustomer)

def add_User(**kwargs):
    pw = kwargs.pop("password")
    u = add_instance(User, **kwargs)
    u.set_password(pw)
    u.save()
    return u


def try_delete(item):
    """
    Tries to delete an item without exploding
    """
    try:
        if item.pk:
            item.delete()
    except ObjectDoesNotExist:
        pass


class TestHelpersMixin(object): 
    def assertObjectMatchesData(self, ob, data, msg=''):
        for key, value in data.iteritems():
            n_msg = msg + ' data["{0}"] != ob.{0}'.format(key)
            self.assertEquals(getattr(ob, key), value, n_msg)
