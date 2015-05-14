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
    s.save()
    return s


add_Company = partial(add_instance, models.Company)
add_Item = partial(add_instance, models.Item)
add_Customer = partial(add_instance, models.Customer)
add_CompanyUser = partial(add_instance, models.CompanyUser)
add_Bill = partial(add_instance, models.Bill)
add_BillItem = partial(add_instance, models.BillItem)


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
