from django.db import models
from django.contrib.auth.models import User


class Shop(models.Model):
    """
    Represents a shop
    """
    name = models.CharField(max_length=100, unique=True)

    def __unicode__(self):
        return self.name


class ShopUser(models.Model):
    """
    Represents a shop clerk that has an associated shop and user account
    He can log in and user the facilities for the associated shop
    """
    shop = models.ForeignKey(Shop)
    user = models.OneToOneField(User)

    def __unicode__(self):
        return self.user.username


class BaseItem(models.Model):
    """
    Represents an abstract stock item
    """
    sku = models.CharField(max_length=50)
    name = models.CharField(max_length=50)
    description = models.CharField(max_length=500)
    shop = models.ForeignKey(Shop)

    def __unicode__(self):
        return "{} ({})".format(self.name, self.pk)


class Item(BaseItem):
    """
    Represents an item that can be sold or bought
    """
    pass


class Customer(models.Model):
    """
    Represents a customer
    """
    name = models.CharField(max_length=100)

    def __unicode__(self):
        return self.name


class Bill(models.Model):
    """
    Represents a bill
    """
    issued_to = models.ForeignKey(Customer, blank=True)
    number = models.CharField(max_length=20, blank=True)
    shop = models.ForeignKey(Shop)
    is_proforma = models.BooleanField(default=True)

    @property
    def items(self):
        return BillItem.objects.filter(bill=self, shop=self.shop)

    def __unicode__(self):
        return self.number

    def can_be_modified(self):
        """
        Returns True or False if the bill is definitive or not
        """
        return self.is_proforma

    def save(self, *args, **kwargs):
        """
        Tries to save the new values, but doesn't do anything it the bill can't be modified
        """
        try:
            if Bill.objects.get(pk=self.pk).can_be_modified():
                super(Bill, self).save(*args, **kwargs)
        except Bill.DoesNotExist:
            super(Bill, self).save(*args, **kwargs)

    def secret_save(self, *args, **kwargs):
        """
        Does the save() without checking
        """
        super(Bill, self).save(*args, **kwargs)


class BillItem(BaseItem):
    """
    Represents an intem in a bill
    """
    bill = models.ForeignKey(Bill)
    qty = models.IntegerField()

    def __unicode__(self):
        return "{} x {}".format(self.sku, self.qty)

    def save(self, *args, **kwargs):
        """
        Tries to save the new values, but doesn't do anything it the bill can't be modified
        """
        try:
            prev_item = BillItem.objects.get(pk=self.pk)
            if prev_item.bill.can_be_modified():
                super(BillItem, self).save(*args, **kwargs)
        except BillItem.DoesNotExist:
            super(BillItem, self).save(*args, **kwargs)

    def secret_save(self, *args, **kwargs):
        """
        Does the save() without checking
        """
        super(BillItem, self).save(*args, **kwargs)
