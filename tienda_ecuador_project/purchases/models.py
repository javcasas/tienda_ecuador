# * encoding: utf-8 *
from datetime import date, timedelta, datetime
import json
import pytz

from django.db import models
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.core.files.storage import FileSystemStorage

from util import signature
from stakeholders import models as stakeholders


class Purchase(models.Model):
    """
    A licence model
    """
    date = models.DateField(
        default=date.today)
    xml_content = models.DateField(
        default=date.today)
    seller = models.ForeignKey(
        stakeholders.Seller)
