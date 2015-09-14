from datetime import datetime
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


current_ruc = count(10)
get_ruc = lambda: str(current_ruc.next())


def get_date():
    return datetime.now(tz=pytz.timezone('America/Guayaquil'))

