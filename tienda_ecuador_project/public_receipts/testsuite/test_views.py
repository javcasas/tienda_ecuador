# * encoding: utf-8 *
from datetime import datetime, date
from decimal import Decimal
import pytz
import xml.etree.ElementTree as ET

from django.test import TestCase, Client
from django.core.urlresolvers import reverse

import billing.models

from util.testsuite.helpers import add_instance, TestHelpersMixin


def get_date():
    now = datetime.now(tz=pytz.timezone('America/Guayaquil'))
    return now.replace(microsecond=0)


def fix_keys(keys):
    bad_keys = ['date']
    return [k for k in keys if k not in bad_keys]


class ReceiptViewTests(TestCase, TestHelpersMixin):
    """
    Tests that check that the models have all the required fields
    """
    def setUp(self):
        self.company = add_instance(
            billing.models.Company,
            **billing.testsuite.test_models.base_data['Company'])

        self.bill_data = dict(
            number='33344556677',
            xml_content='xml',
            numero_autorizacion='12342423423',
            ambiente_sri='pruebas',
            iva=Decimal(3),
            total_sin_iva=Decimal(15),
            clave_acceso='4545454545',
            iva_retenido=Decimal(0))

        self.bill = add_instance(
            billing.models.Bill,
            company=self.company,
            date=get_date(),
            fecha_autorizacion=date(2015, 5, 1),
            ride_content='ride',  # FIXME, should be in response
            issues='asdf',  # FIXME, should be in response
            **self.bill_data)

    def test_show_form(self):
        """
        Checks the form for getting receipts
        """
        c = Client()
        r = c.get(reverse('public-receipts:index'))
        self.assertContainsTag(r, tag_name='input',
                               name='clave', type='text',
                               placeholder='Clave de Acceso')

    def test_receipt_not_found(self):
        clave_acceso = '123123123'
        r = self.simulate_post(
            reverse('public-receipts:index'),
            {'clave': clave_acceso},
            Client(),
            follow=True)
        self.assertContains(r, "No encontrado")
        self.assertContains(r, "No se encontró ningún comprobante con la clave " + clave_acceso)

    def test_receipt_found(self):
        clave_acceso = '4545454545'
        r = self.simulate_post(
            reverse('public-receipts:index'),
            {'clave': clave_acceso},
            Client(),
            follow=True)
        for key, val in self.bill_data.iteritems():
            self.assertContains(r, val, msg_prefix="Data '{}': '{}' not found on response".format(key, val))
