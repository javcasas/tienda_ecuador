from datetime import datetime, date, timedelta
from itertools import count
import pytz

from django.test import TestCase
from django.core.exceptions import ValidationError

from sri.testsuite.test_models import MakeBaseInstances
from company_accounts import models

from helpers import (add_instance,
                     add_User,
                     TestHelpersMixin)


current_ruc = count(10)
get_ruc = lambda: str(current_ruc.next())


def get_date():
    return datetime.now(tz=pytz.timezone('America/Guayaquil'))

base_data = {
    "Company": {
        "nombre_comercial": "Tienda 1",
        "ruc": '1234567890001',
        "razon_social": "Paco Pil",
        "direccion_matriz": "C del pepino",
        "contribuyente_especial": "",
        'siguiente_numero_proforma': 4,
        'cert': '',
        'key': '',
    },
    "Establecimiento": {
        "codigo": "001",
        "direccion": "C del pepino",
        "descripcion": "Madre",
    },
    "PuntoEmision": {
        "codigo": "001",
        "descripcion": "Caja principal",
        'siguiente_secuencial_pruebas': 1,
        'siguiente_secuencial_produccion': 1,
    },
}

class MakeBaseInstances(MakeBaseInstances):
    def setUp(self):
        super(MakeBaseInstances, self).setUp()
        self.company = add_instance(models.Company, **base_data['Company'])

        self.establecimiento = add_instance(models.Establecimiento,
                                            company=self.company,
                                            **base_data['Establecimiento'])

        self.punto_emision = add_instance(models.PuntoEmision,
                                          establecimiento=self.establecimiento,
                                          **base_data['PuntoEmision'])

        self.user = add_User(username="Paco", password='')
        self.company_user = add_instance(models.CompanyUser,
                                         company=self.company,
                                         user=self.user)


class FieldsTests(MakeBaseInstances, TestCase, TestHelpersMixin):
    """
    Tests that check if a given model has all the required fields
    """
    def setUp(self):
        super(FieldsTests, self).setUp()

        self.tests = [
            (models.Company, base_data['Company'],
                {"razon_social": "Pepe Pil",
                 "ruc": "3333333333",
                 "nombre_comercial": "453534"}),
            (models.CompanyUser, {},
                {'company': self.company,
                 'user': self.user}),
            (models.Establecimiento, base_data['Establecimiento'],
                {'company': self.company}),
            (models.PuntoEmision, base_data['PuntoEmision'],
                {'establecimiento': self.establecimiento}),
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


class UnicodeTests(TestCase, TestHelpersMixin):
    pass


class CompanyUserTests(MakeBaseInstances, TestCase, TestHelpersMixin):
    def test_unicode(self):
        self.assertEquals(str(self.company_user),
                          self.company_user.user.username)


class LicenceTests(MakeBaseInstances, TestHelpersMixin):
    def test_initial_licence(self):
        licence = self.company.licence
        self.assertEquals(licence.effective_licence, 'demo')
        self.assertEquals(licence.days_to_expiration, 0)
        self.assertEquals(str(licence), 'Demo')

    def test_set_next_licence(self):
        licence = self.company.licence
        licence.approve('professional', date(2020, 10, 10))
        self.assertEquals(licence.effective_licence, 'professional')
        self.assertEquals(type(licence.days_to_expiration), int)
        self.assertTrue(licence.days_to_expiration > 20)
        self.assertEquals(str(licence), "Professional")

    def almost_expired_licence(self):
        licence = self.company.licence
        licence.next_licence = 'professional'
        licence.save()
        licence.approve(date.today())
        self.assertEquals(licence.effective_licence, 'professional')
        self.assertEquals(licence.days_to_expiration, 0)
        self.assertFalse(licence.expired)
        self.assertEquals(str(licence), "Professional")

    def expired_licence(self):
        licence = self.company.licence
        licence.next_licence = 'professional'
        licence.save()
        licence.approve(date.today() - timedelta(days=3))
        self.assertEquals(licence.effective_licence, 'demo')
        self.assertEquals(licence.days_to_expiration, 0)
        self.assertTrue(licence.expired)
        self.assertEquals(str(licence), "Licencia Caducada")
