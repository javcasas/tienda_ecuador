from datetime import datetime
from decimal import Decimal
import pytz

from django.test import TestCase
from django.core.exceptions import ValidationError

from inventory import models

from company_accounts.testsuite.test_models import make_base_instances as company_accounts_make_base_instances

from util.testsuite.helpers import (add_instance,
                                    TestHelpersMixin)


def get_date():
    return datetime.now(tz=pytz.timezone('America/Guayaquil'))

base_data = {
    "Item": {
        'name': "Test Item",
        'code': "12345",
        'description': "No desc",
        'tipo': 'producto',
        'decimales_qty': 0,
    },
}


class MakeBaseInstances(object):
    def setUp(self):
        self.__dict__.update(company_accounts_make_base_instances())
        self.item = add_instance(
            models.Item,
            name="Test Item",
            code="12345",
            description="No desc",
            tipo='producto',
            decimales_qty=0,
            company=self.company)
        self.batch = add_instance(
            models.Batch,
            item=self.item,
            unit_cost=Decimal(5),
            code='444',
            acquisition_date=get_date())
        self.sku = add_instance(
            models.SKU,
            batch=self.batch,
            qty=Decimal(10),
            unit_price=Decimal(20),
            establecimiento=self.establecimiento,
            location="In the backyard")


class FieldsTest(MakeBaseInstances, TestCase, TestHelpersMixin):
    """
    Tests that check if a given model has all the required fields
    """
    def setUp(self):
        super(FieldsTest, self).setUp()

        self.tests = [
            (models.Item, base_data['Item'],
                {"company": self.company,
                 }),
        ]

    def test_all_clases(self):
        for cls, data, updates in self.tests:
            mydata = data.copy()
            mydata.update(updates)
            self.assertHasAllTheRequiredFields(cls, mydata)

    def assertHasAllTheRequiredFields(self, cls, data):
        """
        Actually tests if all the required fields are there
        """
        ob = cls(**data)
        try:
            ob.full_clean()
        except ValidationError as e:
            self.fail("Error testing {}: {}".format(cls, e))
        try:
            save = ob.secret_save
        except AttributeError:
            save = ob.save
        save()
        msg = str(cls)
        self.assertObjectMatchesData(cls.objects.get(id=ob.id), data, msg)


class ItemTests(MakeBaseInstances, TestCase, TestHelpersMixin):
    """
    Tests for the Item classes
    """
    def test_unicode(self):
        """
        Prueba str() y unicode()
        """
        self.assertEquals(str(self.item), "12345 - Test Item")
