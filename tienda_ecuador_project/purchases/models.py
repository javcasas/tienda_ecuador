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
    Model for purchases
    """
    date = models.DateField(
        default=date.today)
    xml_content = models.FileField(
        )
    seller = models.ForeignKey(
        stakeholders.Seller)
    closed = models.BooleanField(
        default=False)
    comment = models.TextField(
        blank=True)
    number = models.CharField(max_length=20, blank=True)
