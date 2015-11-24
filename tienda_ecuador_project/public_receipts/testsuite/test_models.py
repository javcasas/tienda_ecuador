from datetime import datetime, date
from itertools import count
from decimal import Decimal
import pytz

from django.test import TestCase
from django.core.exceptions import ValidationError

from helpers import (add_instance,
                     add_User,
                     add_Company,
                     add_ProformaBill,
                     add_Bill,
                     add_Customer,
                     TestHelpersMixin)

import billing.models
import billing.testsuite.test_models


current_ruc = count(10)
get_ruc = lambda: str(current_ruc.next())


def get_date():
    return datetime.now(tz=pytz.timezone('America/Guayaquil'))

class FieldsTests(TestCase):
    """
    Tests that check that the models have all the required fields
    """
    def setUp(self):
        self.company = add_Company(**billing.testsuite.test_models.base_data['Company'])


    def test_fields_bill(self):
        """
        Checks that the bill has all the required fields
        """
        bill = billing.models.Bill(
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

        self.assertEquals(bill.number, '33344556677')

        self.assertEquals(bill.xml_content, 'xml')
        self.assertEquals(bill.ride_content, 'ride')

        self.assertEquals(bill.fecha_autorizacion, date(2015, 5, 1))
        self.assertEquals(bill.numero_autorizacion, '12342423423')

        self.assertEquals(bill.ambiente_sri, 'pruebas')

        self.assertEquals(bill.clave_acceso, '4545454545')
        self.assertEquals(bill.issues, 'asdf')
