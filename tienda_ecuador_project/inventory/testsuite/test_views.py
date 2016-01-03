import json

from django.test import TestCase
from django.core.urlresolvers import reverse

from company_accounts.testsuite.test_views import LoggedInWithCompanyTests
from test_models import MakeBaseInstances


class JSONTests(LoggedInWithCompanyTests, MakeBaseInstances, TestCase):
    def test_sku_json(self):
        r = self.c.get(reverse('sku_establecimiento_list_json',
                               args=(self.establecimiento.id,)))
        data = json.loads(r.content)
        self.assertEquals(
            data,
            [
                {u'code': u'12345-444',
                 u'name': u'Test Item',
                 u'unit_price': 20.0,
                 u'qty': 10.0,
                 u'location': u'In the backyard',
                 u'id': 1}
            ])
