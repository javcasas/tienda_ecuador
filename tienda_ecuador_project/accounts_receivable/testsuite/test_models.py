from datetime import datetime, date, timedelta
from itertools import count
from decimal import Decimal
import pytz

from django.test import TestCase
from django.core.exceptions import ValidationError

import accounts_receivable.models as models
import billing.models
from billing.testsuite.test_models import base_data as billing_base_data

current_ruc = count(10)
get_ruc = lambda: str(current_ruc.next())


def get_date():
    return date.today()

class ReceivableTests(TestCase):
    def setUp(self):
        self.company = billing.models.Company.objects.get_or_create(**billing_base_data['Company'])[0]
        self.bill = billing.models.Bill.objects.get_or_create(
            company=self.company,
            **billing_base_data['Bill'])[0]
        self.payment_method = billing.models.FormaPago.objects.get_or_create(codigo="33", descripcion="Efectivo")[0]

    def test_amount_left(self):
        """
        Tests the amount_left property
        """
        r = models.Receivable(qty=Decimal(100),
                              bill=self.bill,
                              date=get_date(),
                              method=self.payment_method,
                              comment='')
        r.save()
        # No payments yet
        self.assertEquals(r.amount_left, Decimal(100))

        # Partial payment
        models.Payment(receivable=r,
                       date=get_date(),
                       qty=Decimal(60),
                       method=self.payment_method).save()
        self.assertEquals(r.amount_left, Decimal(40))

        # Full payment
        models.Payment(receivable=r,
                       date=get_date(),
                       qty=Decimal(40),
                       method=self.payment_method).save()
        self.assertEquals(r.amount_left, Decimal(0))

    def test_days_left(self):
        """
        Tests the days_left property
        """
        r = models.Receivable(qty=Decimal(100),
                              bill=self.bill,
                              date=get_date(),
                              method=self.payment_method,
                              comment='')
        self.assertEquals(r.days_left, 0)

        r = models.Receivable(qty=Decimal(100),
                              bill=self.bill,
                              date=get_date() + timedelta(days=5),
                              method=self.payment_method,
                              comment='')
        self.assertEquals(r.days_left, 5)

    def test_payments(self):
        """
        Tests the payments property
        """
        r = models.Receivable(qty=Decimal(100),
                              bill=self.bill,
                              date=get_date(),
                              method=self.payment_method,
                              comment='')
        r.save()
        payment = models.Payment(receivable=r,
                       date=get_date(),
                       qty=Decimal(60),
                       method=self.payment_method)
        payment.save()
        self.assertEquals(list(r.payments), [payment])

    def test_unicode(self):
        """
        Tests the amount_left property
        """
        r = models.Receivable(qty=Decimal(100),
                                      bill=self.bill,
                                      date=get_date(),
                                      method=self.payment_method,
                                      comment='')
        self.assertEquals(
            unicode(r),
            "{}/{} - ${}".format(r.bill.number, r.date, r.amount_left))
