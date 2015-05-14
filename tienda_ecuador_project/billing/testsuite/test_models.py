from django.test import TestCase
from billing.models import Bill, Company, Customer, BillItem, CompanyUser
from django.contrib.auth.models import User
from helpers import (add_Company, add_Item, add_Customer,
                     add_CompanyUser, add_Bill, add_BillItem,
                     add_User, try_delete)


class BillTests(TestCase):
    """
    Tests that check the Bill model
    """
    def setUp(self):
        self.company = add_Company(name="Tienda 1")
        self.customer = add_Customer(name="Pepe", company=self.company)

    def tearDown(self):
        for i in [self.company, self.customer]:
            try_delete(i)

    def test_bill_has_all_the_required_fields(self):
        """
        Checks that the bill model has all the required fields
        """
        pbill = add_Bill(company=self.company, number=3,
                         issued_to=self.customer, is_proforma=True)
        bill = Bill.objects.get(pk=pbill.pk)
        self.assertEquals(bill.company, self.company)
        self.assertEquals(bill.number, '3')
        self.assertEquals(bill.issued_to, self.customer)
        self.assertEquals(bill.is_proforma, True)
        pbill.delete()

    def test_BillItem_has_all_the_required_fields(self):
        """
        Checks that the BillItem model has all the required fields
        """
        bill = add_Bill(company=self.company, number=3,
                        issued_to=self.customer, is_proforma=True)
        pitem = add_BillItem(bill=bill, qty=6,
                             sku="SKU45", name="Item",
                             description="Desc", company=self.company)
        item = BillItem.objects.get(pk=pitem.pk)
        self.assertEquals(item.bill, bill)
        self.assertEquals(item.qty, 6)
        self.assertEquals(item.sku, "SKU45")
        self.assertEquals(item.name, "Item")
        self.assertEquals(item.description, "Desc")
        self.assertEquals(item.company, self.company)

    def test_Bill_str(self):
        """
        Bill.str, unicode methods
        """
        bill = Bill(company=self.company, number=3,
                    issued_to=self.customer, is_proforma=True)
        self.assertEquals(str(bill), "3 - Pepe")

    def test_BillItem_str(self):
        """
        BillItem.str, unicode methods
        """
        bill = add_Bill(company=self.company, number=3,
                        issued_to=self.customer, is_proforma=True)
        item = add_BillItem(bill=bill, qty=6,
                            sku="SKU45", name="Item",
                            description="Desc", company=self.company)
        self.assertEquals(str(item), "SKU45 x 6")

    def test_bill_can_be_written_if_is_proforma(self):
        """
        Checks that the bill can be written if is proforma
        """
        bill = add_Bill(company=self.company, number=3,
                        issued_to=self.customer, is_proforma=True)
        self.assertEqual(Bill.objects.get(pk=bill.pk).number, '3')
        bill.number = 4
        bill.save()
        self.assertEqual(Bill.objects.get(pk=bill.pk).number, '4')

    def test_bill_is_final(self):
        """
        Checks that the bill can only be written if is proforma
        """
        bill = add_Bill(company=self.company, number=3,
                        issued_to=self.customer, is_proforma=True)
        bill.is_proforma = False
        bill.save()
        bill.number = 4
        bill.save()
        self.assertEqual(Bill.objects.get(pk=bill.pk).number, '3')

    def test_bill_secret_save(self):
        """
        Checks Bill.secret_save
        """
        bill = add_Bill(company=self.company, number=5,
                        issued_to=self.customer, is_proforma=False)
        bill.number = 6
        bill.secret_save()
        self.assertEqual(Bill.objects.get(pk=bill.pk).number, '6')

    def test_can_add_item_to_proforma_bill(self):
        """
        Checks that I can add items to a proforma bill
        """
        bill = add_Bill(company=self.company, number=3,
                        issued_to=self.customer, is_proforma=True)
        item = add_BillItem(bill=bill, qty=6,
                            sku="SKU45", name="Item",
                            description="Desc", company=self.company)
        self.assertEqual(BillItem.objects.get(pk=item.pk).qty, 6)

    def test_cant_add_item_to_final_bill(self):
        """
        Checks that I can't add items to a final bill
        """
        bill = add_Bill(company=self.company, number=3,
                        issued_to=self.customer, is_proforma=False)
        item = add_BillItem(bill=bill, qty=6,
                            sku="SKU45", name="Item",
                            description="Desc", company=self.company)
        with self.assertRaises(BillItem.DoesNotExist):
            BillItem.objects.get(pk=item.pk)

    def test_can_edit_item_in_proforma_bill(self):
        """
        Checks that I can add items to a proforma bill
        """
        bill = add_Bill(company=self.company, number=3,
                        issued_to=self.customer, is_proforma=True)
        item = add_BillItem(bill=bill, qty=6,
                            sku="SKU45", name="Item",
                            description="Desc", company=self.company)
        item.qty = 8
        item.save()
        self.assertEqual(BillItem.objects.get(pk=item.pk).qty, 8)

    def test_bill_item_secret_save(self):
        """
        Checks that I can't add items to a final bill
        """
        bill = add_Bill(company=self.company, number=3,
                        issued_to=self.customer, is_proforma=False)
        item = BillItem(bill=bill, qty=6,
                        sku="SKU45", name="Item",
                        description="Desc", company=self.company)
        item.secret_save()
        self.assertEquals(BillItem.objects.get(pk=item.pk).qty, 6)

    def test_bill_items(self):
        """
        Checks the Bill.items method
        """
        bill = add_Bill(company=self.company, number=3,
                        issued_to=self.customer, is_proforma=True)
        item = add_BillItem(bill=bill, qty=6,
                            sku="SKU45", name="Item",
                            description="Desc", company=self.company)
        self.assertEqual(bill.items[0], item)


class CompanyTests(TestCase):
    """
    Tests that check the Company model
    """
    def test_Company_has_all_the_required_fields(self):
        pc = add_Company(name="Tienda 1")
        company = Company.objects.get(pk=pc.pk)
        self.assertEquals(company.name, "Tienda 1")
        pc.delete()

    def test_Company_str(self):
        c = Company(name="Tienda 1")
        self.assertEquals(str(c), "Tienda 1")


class CompanyUserTests(TestCase):
    """
    Tests that check the CompanyUser model
    """
    def setUp(self):
        self.company = add_Company(name="Tienda 1")
        self.user = add_User(username="Pepe", password='bleh')

    def tearDown(self):
        for i in [self.company, self.user]:
            try_delete(i)

    def test_CompanyUser_has_all_the_required_fields(self):
        pcu = add_CompanyUser(company=self.company, user=self.user)
        cu = CompanyUser.objects.get(pk=pcu.pk)
        self.assertEquals(cu.company, self.company)
        self.assertEquals(cu.user, self.user)
        pcu.delete()

    def test_CompanyUser_str(self):
        cu = CompanyUser(company=self.company, user=self.user)
        self.assertEquals(str(cu), self.user.username)


class CustomerTests(TestCase):
    """
    Tests that check the Customer model
    """
    def setUp(self):
        self.company = add_Company(name="Tienda 1")

    def tearDown(self):
        self.company.delete()

    def test_Customer_has_all_the_required_fields(self):
        pcust = add_Customer(name="Pepe", company=self.company)
        cust = Customer.objects.get(pk=pcust.pk)
        self.assertEquals(cust.name, "Pepe")
        cust.delete()

    def test_Customer_str(self):
        cust = Customer(name="Pepe", company=self.company)
        self.assertEquals(str(cust), "Pepe")
