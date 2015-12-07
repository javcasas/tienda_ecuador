# * encoding: utf-8 *
from datetime import datetime, date
from decimal import Decimal
import pytz
import xml.etree.ElementTree as ET

from django.test import TestCase, Client
from django.core.urlresolvers import reverse

import billing.models
import billing.testsuite.test_models

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
            numero_autorizacion='12342423423',
            ambiente_sri='pruebas',
            clave_acceso='4545454545',
            )

        self.bill = add_instance(
            billing.models.Bill,
            company=self.company,
            date=get_date(),
            xml_content='<xml>stufff</xml>',
            fecha_autorizacion=date(2015, 5, 1),
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
        # XML and RIDE links
        self.assertContains(r, reverse("public-receipts:receipt_view_xml", args=(clave_acceso,)))
        self.assertContains(r, reverse("public-receipts:receipt_view_ride", args=(clave_acceso,)))

    def test_receipt_get_xml(self):
        clave_acceso = '4545454545'
        c = Client()
        r = c.get(
            reverse("public-receipts:receipt_view_xml", args=(clave_acceso,)))
        self.assertEquals(r.content, self.bill.xml_content)
