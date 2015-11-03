# * encoding: utf-8 *
from datetime import date
from decimal import Decimal

from django.db import models
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

from utils import Property, ConvertedProperty


class Receivable(models.Model):
    """
    Amount of money to receive from a payer
    """
    # bill
    # qty
    # payment date
    # payment method
    # comment


class Payment(models.Model):
    """
    Represents a payment for a given receivable
    """
    receivable = models.ForeignKey(Receivable)
    # date
    # qty
    # payment method
    # comment
