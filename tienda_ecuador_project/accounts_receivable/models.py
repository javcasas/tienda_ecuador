# * encoding: utf-8 *
from datetime import date
from decimal import Decimal

from django.db import models
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

import billing.models

from utils import Property, ConvertedProperty


class Receivable(models.Model):
    """
    Amount of money to receive from a payer
    """
    bill = models.ForeignKey(billing.models.Bill)
    qty = models.DecimalField(max_digits=20, decimal_places=8)
    date = models.DateField()
    method = models.ForeignKey(billing.models.FormaPago)
    received = models.BooleanField(default=False)
    comment = models.TextField(blank=True)

    @property
    def total_paid(self):
        """
        Total paid
        """
        return sum([p.qty for p in self.payments])

    @property
    def amount_left(self):
        """
        Amount left to pay
        """
        return self.qty - self.total_paid

    @property
    def days_left(self):
        """
        Number of days left to pay
        """
        return (self.date - date.today()).days

    @property
    def payments(self):
        return Payment.objects.filter(receivable=self)

    def get_absolute_url(self):
        return reverse("receivable_detail", args=(self.id,))


class Payment(models.Model):
    """
    Represents a payment for a given receivable
    """
    receivable = models.ForeignKey(Receivable)
    date = models.DateField()
    qty = models.DecimalField(max_digits=20, decimal_places=8)
    method = models.ForeignKey(billing.models.FormaPago)
    comment = models.TextField(blank=True)
