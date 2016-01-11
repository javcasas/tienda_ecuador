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


