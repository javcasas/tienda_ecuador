from datetime import datetime, date
from decimal import Decimal
import base64
import pytz
import xml.etree.ElementTree as ET

from django.test import TestCase, Client
from django.core.urlresolvers import reverse

import accounts_receivable.models as models
import billing.models
import company_accounts.models
from billing.testsuite.test_views import LoggedInTests
from billing.testsuite.test_models import base_data as billing_base_data
from test_models import get_date


class ReceivableTests(LoggedInTests):
    def setUp(self):
        super(ReceivableTests, self).setUp()
        self.company = company_accounts.models.Company.objects.get_or_create(**billing_base_data['Company'])[0]
        self.cu = company_accounts.models.CompanyUser.objects.get_or_create(company=self.company, user=self.user)[0]
        self.bill = billing.models.Bill.objects.get_or_create(
            company=self.company,
            **billing_base_data['Bill'])[0]
        self.payment_method = billing.models.FormaPago.objects.get_or_create(codigo="33", descripcion="Efectivo")[0]

    def test_index_empty(self):
        r = self.c.get(
            reverse("accounts_receivable_index", args=(self.company.id,)))
        self.assertContains(r, "No hay cuentas por cobrar")

    def test_index_single_item(self):
        t = models.Receivable(qty=Decimal(100),
                              bill=self.bill,
                              date=get_date(),
                              method=self.payment_method,
                              comment='')
        t.save()
        models.Payment(receivable=t,
                       date=get_date(),
                       qty=Decimal("66.66"),
                       method=self.payment_method).save()

        r = self.c.get(
            reverse("accounts_receivable_index", args=(self.company.id,)))
        self.assertContains(r, "danger")  # CSS class
        self.assertContains(r, t.bill.number)
        self.assertContains(r, t.date)
        self.assertContains(r, t.qty)
        self.assertContains(r, t.amount_left)

    def test_index_no_items_left(self):
        t = models.Receivable(qty=Decimal(100),
                              bill=self.bill,
                              date=get_date(),
                              method=self.payment_method,
                              received=True,
                              comment='')
        t.save()

        r = self.c.get(
            reverse("accounts_receivable_index", args=(self.company.id,)))
        self.assertContains(r, "No hay cuentas por cobrar")

    def test_receivable_detail(self):
        t = models.Receivable(qty=Decimal(100),
                              bill=self.bill,
                              date=get_date(),
                              method=self.payment_method,
                              received=True,
                              comment='Comentario comentario')
        t.save()
        p = models.Payment(receivable=t,
                           date=get_date(),
                           qty=Decimal("66.66"),
                           method=self.payment_method,
                           comment='Otro comentario')
        p.save()

        r = self.c.get(
            reverse("receivable_detail", args=(t.id,)))
        self.assertContains(r, t.bill.number)
        self.assertContains(r, t.date)
        self.assertContains(r, t.qty)
        self.assertContains(r, t.amount_left)
        self.assertContains(r, t.method.descripcion)
        self.assertContains(r, "Cobrado" if t.received else "No Cobrado")
        self.assertContains(r, t.comment)

        self.assertContains(r, p.date)
        self.assertContains(r, p.qty)
        self.assertContains(r, p.method.descripcion)
        self.assertContains(r, p.comment)
