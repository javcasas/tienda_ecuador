from django.test import TestCase
from django.core.exceptions import ValidationError

from company_accounts.testsuite.test_models import MakeBaseInstances
from stakeholders import models

from util.testsuite.helpers import (add_instance,
                                    TestHelpersMixin)


base_data = {
    "BaseCustomer": {
        "razon_social": "Pepe",
        "tipo_identificacion": "ruc",
        "identificacion": "1713831152001",
        "email": "papa@ble.com",
        "direccion": "dfdf gfwergwer",
    }
}


class MakeBaseInstances(MakeBaseInstances):
    def setUp(self):
        super(MakeBaseInstances, self).setUp()
        self.customer = add_instance(
            models.Customer,
            company=self.company,
            **base_data['BaseCustomer'])
