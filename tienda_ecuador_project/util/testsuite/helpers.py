from contextlib import contextmanager
import urllib
import xml.etree.ElementTree as ET

from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.test import Client


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

    def assertContainsObject(self, response, item, fields, msg=None):
        """
        Checks all the fields in a general object
        """
        for field in fields:
            value = getattr(item, field)
            self.assertContains(
                response, str(value), html=False,
                msg_prefix='Field {} ({}) not found'.format(field, value))

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

    def simulate_post(self, url, data_to_post, client=None, form_index=0):
        """
        Simulates a post
            Only commits data that is not in hidden fields
        """
        client = client or self.c
        source_html = client.get(url).content
        try:
            root = ET.fromstring(source_html)
        except ET.ParseError:
            open("test.xml", "w").write(source_html)
            raise
        data_to_post = make_post(data_to_post)
        data_to_use = {}

        current_form = root.findall(".//form")[form_index]
        # input fields, including hidden inputs
        for i in current_form.findall(".//input"):
            key = i.get('name')
            pre_value = i.get('value')
            type_ = i.get('type')
            # Pre-filled in values
            data_to_use[key] = pre_value or ""
            # Added values
            if type_ != "hidden" and data_to_post.get(key):
                data_to_use[key] = data_to_post.pop(key)
            if type_ == 'hidden' and data_to_post.get(key):
                self.fail(
                    "Test error: Attempt to post custom"
                    " value for hidden field: {} = {}".format(
                        key, data_to_post[key]))

        # textarea fields
        textareas = current_form.findall(".//textarea")
        for ta in textareas:
            key = ta.get('name')
            data_to_use[key] = data_to_post.pop(key, ta.text)

        # select fields
        selects = current_form.findall(".//select")
        for s in selects:
            key = s.get('name')
            selected_option = root.findall(
                ".//form//select[@name='{}']"
                "/option[@selected]".format(key))
            default = selected_option[0].get("value") if selected_option else ""
            data_to_use[key] = data_to_post.pop(key, default)

        # submit buttons
        buttons = current_form.findall(".//button")
        for bt in buttons:
            key = bt.get('name')
            value = bt.get('value')
            if str(data_to_post.get(key)) == value:
                data_to_use[key] = data_to_post.pop(key)
                break

        self.assertFalse(data_to_post,
                         "Items left in data to post: {}".format(data_to_post))
        return client.post(url, data_to_use)

    def assertContainsTag(self, response, tag_name, **attributes):
        """
        Ensures the response contains the specified tag
        with the specified attributes
        """
        try:
            root = ET.fromstring(response.content)
        except:
            open("test.xml", "w").write(response.content)
            raise

        def valid_tag(tag):
            for key, val in attributes.iteritems():
                if key not in tag.attrib:
                    return False
                if tag.attrib[key] != val:
                    return False
            else:
                return True

        tags = root.findall(".//" + tag_name)
        for tag in tags:
            if valid_tag(tag):
                return True
        else:
            attrs = ["{}='{}'".format(key, val)
                     for key, val in attributes.iteritems()]
            self.fail("Tag {} with attrs {} not found".format(
                      tag_name, " ".join(attrs)))


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


class LoggedInTests(object):
    """
    Tests that support a logged-in user
    """
    def setUp(self):
        super(LoggedInTests, self).setUp()
        self.c = Client()
        r = self.c.post("/accounts/login/",
                        {'username': self.user.username,
                         'password': "paco_pw"},
                        follow=True)
        self.assertRedirects(r, reverse('company_accounts:company_main_menu',
                                        args=(self.company.id,)))

    def tearDown(self):
        self.assert_no_broken_urls()
        super(LoggedInTests, self).tearDown()

    def assert_no_broken_urls(self):
        for model in self.__dict__.values():
            try:
                obs = model.objects.all
                for ob in obs:
                    ob.get_absolute_url()
            except AttributeError:
                # Not a model, or no absolute URL
                continue
            for ob in obs:
                r = self.c.get(ob.get_absolute_url())
                self.assertIn(r.status_code, [200, 404, 405])
