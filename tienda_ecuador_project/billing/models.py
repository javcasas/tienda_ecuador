from django.db import models
from django.contrib.auth.models import User

class ReadOnlyObject(Exception):
    """
    Exception for when trying to write read-only objects
    """

class ReadOnlyMixin(object):
    """
    A mixin that disables overwriting or deleting objects
    """
    def save(self, *args, **kwargs):
        """
        Disable save
        """
        if self.id:
            raise ReadOnlyObject("{} can't be saved".format(self.__class__))
        else:
            return models.Model.save(self, *args, **kwargs)

    def secret_save(self, *args, **kwargs):
        """
        Secret save does save
        """
        return models.Model.save(self, *args, **kwargs)

    def delete(self, *args, **kwargs):
        """
        Disable delete
        """
        raise ReadOnlyObject("{} can't be deleted".format(self.__class__))

    def secret_delete(self, *args, **kwargs):
        """
        Secret delete does delete
        """
        return models.Model.delete(self, *args, **kwargs)


class Company(models.Model):
    """
    Represents a company
    """
    name = models.CharField(max_length=100, unique=True)
    sri_ruc = models.CharField(max_length=100, unique=True)
    sri_razon_social = models.CharField(max_length=100, unique=True)

    def __unicode__(self):
        return self.name


class CompanyUser(models.Model):
    """
    Represents a shop clerk that has an associated company and user account
    He can log in and user the facilities for the associated company
    """
    company = models.ForeignKey(Company)
    user = models.ForeignKey(User)

    def __unicode__(self):
        return self.user.username


##################################
# Customers
##################################
class BaseCustomer(models.Model):
    """
    Represents a generic customer
    """
    name = models.CharField(max_length=100)

    def __unicode__(self):
        return self.name


class Customer(BaseCustomer):
    """
    Represents a generic customer
    """
    company = models.ForeignKey(Company)

    def __unicode__(self):
        return self.name


class BillCustomer(ReadOnlyMixin, BaseCustomer):
    """
    A customer in a final bill
    """


class ProformaBillCustomer(BaseCustomer):
    """
    A customer in a proforma bill
    """
    def toBillCustomer(self):
        new = BillCustomer(name=self.name)
        new.save()
        return new


#####################################
# Bill
#####################################
class BaseBill(models.Model):
    """
    Represents a generic bill
    """
    number = models.CharField(max_length=20, blank=True)
    company = models.ForeignKey(Company)

    def __unicode__(self):
        return "{} - {}".format(self.number, self.issued_to)


class Bill(ReadOnlyMixin, BaseBill):
    """
    Represents a bill
    """
    issued_to = models.ForeignKey(BillCustomer)


class ProformaBill(BaseBill):
    """
    Represents a proforma bill
    """
    issued_to = models.ForeignKey(ProformaBillCustomer)

    def toBill(self):
        new = Bill(company=self.company,
                   number=self.number,
                   issued_to=self.issued_to.toBillCustomer())
        new.save()
        return new


###########################
# Items
##########################
class BaseItem(models.Model):
    """
    Represents an abstract stock item
    """
    sku = models.CharField(max_length=50)
    name = models.CharField(max_length=50)
    description = models.CharField(max_length=500)


class Item(BaseItem):
    """
    Represents an item that can be sold or bought
    """
    company = models.ForeignKey(Company)


class ProformaBillItem(BaseItem):
    """
    Represents an item in a proforma bill
    """
    proforma_bill = models.ForeignKey(ProformaBill)
    qty = models.DecimalField(max_digits=20, decimal_places=8)

    def toBillItem(self, bill):
        new = BillItem(sku=self.sku, name=self.name,
                       description=self.description,
                       bill=bill, qty=self.qty)
        new.save()
        return new


class BillItem(ReadOnlyMixin, BaseItem):
    """
    Represents an item in a final bill
    """
    bill = models.ForeignKey(Bill)
    qty = models.DecimalField(max_digits=20, decimal_places=8)
