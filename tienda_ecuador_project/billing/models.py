from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class Shop(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __unicode__(self):
        return self.name

class ShopUser(models.Model):
    shop = models.ForeignKey(Shop)
    user = models.OneToOneField(User)
    def __unicode__(self):
        return self.user.username


class Item(models.Model):
    sku = models.CharField(max_length=50)
    name = models.CharField(max_length=50)
    description = models.CharField(max_length=500)
    shop = models.ForeignKey(Shop)

    def __unicode__(self):
        return self.name


class Customer(models.Model):
    name = models.CharField(max_length=100)
    def __unicode__(self):
        return self.name


class Bill(models.Model):
    issued_to = models.ForeignKey(Customer, blank=True)
    number = models.CharField(max_length=20, blank=True)
    shop = models.ForeignKey(Shop)
    def __unicode__(self):
        return self.number
    

class BillItem(Item):
    bill = models.ForeignKey(Bill)
    qty = models.IntegerField()

    def __unicode__(self):
        return "{} x {}".format(self.sku, self.qty)
