from datetime import datetime, date
from decimal import Decimal
import pytz
import xml.etree.ElementTree as ET

from django.test import TestCase, Client
from django.core.urlresolvers import reverse

import billing.models

from util.testsuite.helpers import add_instance


def get_date():
    now = datetime.now(tz=pytz.timezone('America/Guayaquil'))
    return now.replace(microsecond=0)


def fix_keys(keys):
    bad_keys = ['date']
    return [k for k in keys if k not in bad_keys]


class ReceiptViewTests(TestCase):
    """
    Tests that check that the models have all the required fields
    """
    def setUp(self):
        self.company = add_instance(
            billing.models.Company,
            **billing.testsuite.test_models.base_data['Company'])

        self.bill_data = dict(
            company=self.company,
            number='33344556677',
            date=get_date(),
            xml_content='xml',
            ride_content='ride',
            fecha_autorizacion=date(2015, 5, 1),
            numero_autorizacion='12342423423',
            ambiente_sri='pruebas',
            iva=Decimal(3),
            total_sin_iva=Decimal(15),
            clave_acceso='4545454545',
            issues='asdf',
            iva_retenido=Decimal(0))

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

    def test_show_form(self):
        """
        Checks that the bill has all the required fields
        """
        c = Client()
        r = c.get(reverse('public-receipts:index'))
        self.assertContainsTag(r, tag_name='input',
                               name='clave', type='text',
                               placeholder='Clave de Acceso')
