# * encoding: utf-8 *
from datetime import datetime, date, timedelta
import pytz
import json

from django.test import TestCase, Client
from django.core.urlresolvers import reverse
from django.http.response import HttpResponseRedirect

from company_accounts import models, views

from util.testsuite.helpers import (TestHelpersMixin,
                                    add_instance,
                                    add_User,
                                    make_post)

from test_models import MakeBaseInstances


def get_date():
    now = datetime.now(tz=pytz.timezone('America/Guayaquil'))
    return now.replace(microsecond=0)


def fix_keys(keys):
    bad_keys = ['date']
    return [k for k in keys if k not in bad_keys]


