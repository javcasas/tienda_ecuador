from datetime import datetime, date, timedelta
from itertools import count
from decimal import Decimal
import pytz

from django.test import TestCase
from django.core.exceptions import ValidationError

from util.testsuite.helpers import add_instance

import sri.models as models

current_ruc = count(10)
get_ruc = lambda: str(current_ruc.next())

class MakeBaseInstances(object):
    def setUp(self):
        self.iva = add_instance(
            models.Iva,
            descripcion="12%",
            codigo='12',
            porcentaje=Decimal(12.0))

        self.ice = add_instance(
            models.Ice,
            descripcion="Bebidas gaseosas",
            codigo='3051',
            porcentaje=50.0)


class TaxTests(TestCase):
    def test_fields(self):
        data = dict(descripcion='test',
                    codigo='cod',
                    porcentaje=Decimal(12),
                    valor_fijo=Decimal("0.02"))
        n = models.Tax(**data)
        n.full_clean()
        n.save()
        n = models.Tax.objects.get(**data)
        for k, v in data.iteritems():
            self.assertEquals(getattr(n, k), v)

class IceTests(TestCase):
    def test_nonzero(self):
        data = dict(descripcion='No ICE',
                    codigo='cod',
                    porcentaje=Decimal(12),
                    valor_fijo=Decimal("0.02"))
        n = models.Ice(**data)
        self.assertFalse(n)

        data = dict(descripcion='ICE',
                    codigo='cod',
                    porcentaje=Decimal(12),
                    valor_fijo=Decimal("0.02"))
        n = models.Ice(**data)
        self.assertTrue(n)
