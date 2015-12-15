from datetime import datetime, date
from decimal import Decimal
import base64
import pytz
import xml.etree.ElementTree as ET

from django.test import TestCase, Client
from django.core.urlresolvers import reverse

from company_accounts.testsuite.test_views import LoggedInWithCompanyTests


class ReceivableTests(LoggedInWithCompanyTests):
    def setUp(self):
        super(ReceivableTests, self).setUp()
        self.company = company_accounts.models.Company.objects.get_or_create(**billing_base_data['Company'])[0]
        self.cu = company_accounts.models.CompanyUser.objects.get_or_create(company=self.company, user=self.user)[0]
        self.bill = billing.models.Bill.objects.get_or_create(
            company=self.company,
            **billing_base_data['Bill'])[0]
        self.payment_method = billing.models.FormaPago.objects.get_or_create(codigo="33", descripcion="Efectivo")[0]

    def _test_index_empty(self):
        r = self.c.get(
            reverse("accounts_receivable_index", args=(self.company.id,)))
        self.assertContains(r, "No hay cuentas por cobrar")
