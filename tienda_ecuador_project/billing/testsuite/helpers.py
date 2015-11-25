from functools import partial
from contextlib import contextmanager
import urllib

from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist


def add_instance(klass, **kwargs):
    """
    Add a instance of the specified class with the specified arguments,
    and returns it after saving it
    """
    s = klass.objects.get_or_create(**kwargs)[0]
    return s


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
        """
        Checks that every field in the data
        exists in the object and is the same
        """
        for key, value in data.iteritems():
            ob_value = getattr(ob, key)
            n_msg = msg + ' data["{0}"] != ob.{0}, {1} != {2}'.format(key,
                                                                      value,
                                                                      ob_value)
            self.assertEquals(ob_value, value, n_msg)

    @contextmanager
    def new_item(self, kind):
        """
        Finds and returns the new item of the specified kind
        created in the context
        """
        def get_set(model):
            return set(model.objects.all())

        class GetattrProxy(object):
            ob = None

            def __getattr__(self, field):
                return getattr(self.ob, field)

        items = get_set(kind)
        res = GetattrProxy()
        yield res
        new_items = (get_set(kind) - items)
        if len(new_items) != 1:
            self.fail("New item of type {} was not created".format(kind))
        res.ob = new_items.pop()


def make_post(data):
    """
    Converts a data dict into a data dict that can be used in a POST
    """
    def convert_id(f):
        try:
            return f.id
        except:
            return f

    def convert_datetime(f):
        try:
            return f.strftime("%Y-%m-%d %H:%M:%S")
        except:
            return f

    def convert_id_to_bare(k):
        if k.endswith("_id"):
            return k[0:-3]
        else:
            return k
    data = {k: convert_id(v) for (k, v) in data.iteritems()}
    data = {k: convert_datetime(v) for (k, v) in data.iteritems()}
    data = {convert_id_to_bare(k): v for (k, v) in data.iteritems()}
    return data

make_put = urllib.urlencode
