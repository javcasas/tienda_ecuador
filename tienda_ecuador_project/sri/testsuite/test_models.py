from datetime import datetime, date, timedelta
from itertools import count
from decimal import Decimal
import pytz

from django.test import TestCase
from django.core.exceptions import ValidationError

import sri.models as models

current_ruc = count(10)
get_ruc = lambda: str(current_ruc.next())


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
