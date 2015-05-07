from django.test import TestCase
from billing.models import Bill, Shop, Customer, BillItem, ShopUser
from django.contrib.auth.models import User


class BillTests(TestCase):
    """
    Tests that check the Bill model
    """
    def setUp(self):
        self.shop = Shop(name="Tienda 1")
        self.shop.save()
        self.customer = Customer(name="Pepe")
        self.customer.save()

    def tearDown(self):
        self.shop.delete()
        self.customer.delete()

    def test_bill_has_all_the_required_fields(self):
        """
        Checks that the bill model has all the required fields
        """
        pbill = Bill(shop=self.shop, number=3,
                     issued_to=self.customer, is_proforma=True)
        pbill.save()
        bill = Bill.objects.get(pk=pbill.pk)
        self.assertEquals(bill.shop, self.shop)
        self.assertEquals(bill.number, '3')
        self.assertEquals(bill.issued_to, self.customer)
        self.assertEquals(bill.is_proforma, True)
        pbill.delete()

    def test_BillItem_has_all_the_required_fields(self):
        """
        Checks that the BillItem model has all the required fields
        """
        bill = Bill(shop=self.shop, number=3,
                    issued_to=self.customer, is_proforma=True)
        bill.save()
        pitem = BillItem(bill=bill, qty=6,
                         sku="SKU45", name="Item",
                         description="Desc", shop=self.shop)
        pitem.save()
        item = BillItem.objects.get(pk=pitem.pk)
        self.assertEquals(item.bill, bill)
        self.assertEquals(item.qty, 6)
        self.assertEquals(item.sku, "SKU45")
        self.assertEquals(item.name, "Item")
        self.assertEquals(item.description, "Desc")
        self.assertEquals(item.shop, self.shop)

    def test_Bill_str(self):
        """
        Bill.str, unicode methods
        """
        bill = Bill(shop=self.shop, number=3,
                    issued_to=self.customer, is_proforma=True)
        self.assertEquals(str(bill), "3 - Pepe")

    def test_BillItem_str(self):
        """
        BillItem.str, unicode methods
        """
        bill = Bill(shop=self.shop, number=3,
                    issued_to=self.customer, is_proforma=True)
        bill.save()
        item = BillItem(bill=bill, qty=6,
                        sku="SKU45", name="Item",
                        description="Desc", shop=self.shop)
        item.save()
        self.assertEquals(str(item), "SKU45 x 6")

    def test_bill_can_be_written_if_is_proforma(self):
        """
        Checks that the bill can be written if is proforma
        """
        bill = Bill(shop=self.shop, number=3,
                    issued_to=self.customer, is_proforma=True)
        bill.save()
        self.assertEqual(Bill.objects.get(pk=bill.pk).number, '3')
        bill.number = 4
        bill.save()
        self.assertEqual(Bill.objects.get(pk=bill.pk).number, '4')

    def test_bill_is_final(self):
        """
        Checks that the bill can only be written if is proforma
        """
        bill = Bill(shop=self.shop, number=3,
                    issued_to=self.customer, is_proforma=True)
        bill.save()
        bill.is_proforma = False
        bill.save()
        bill.number = 4
        bill.save()
        self.assertEqual(Bill.objects.get(pk=bill.pk).number, '3')

    def test_bill_secret_save(self):
        """
        Checks Bill.secret_save
        """
        bill = Bill(shop=self.shop, number=5,
                    issued_to=self.customer, is_proforma=False)
        bill.save()
        bill.number = 6
        bill.secret_save()
        self.assertEqual(Bill.objects.get(pk=bill.pk).number, '6')

    def test_can_add_item_to_proforma_bill(self):
        """
        Checks that I can add items to a proforma bill
        """
        bill = Bill(shop=self.shop, number=3,
                    issued_to=self.customer, is_proforma=True)
        bill.save()
        item = BillItem(bill=bill, qty=6,
                        sku="SKU45", name="Item",
                        description="Desc", shop=self.shop)
        item.save()
        self.assertEqual(BillItem.objects.get(pk=item.pk).qty, 6)

    def test_cant_add_item_to_final_bill(self):
        """
        Checks that I can't add items to a final bill
        """
        bill = Bill(shop=self.shop, number=3,
                    issued_to=self.customer, is_proforma=False)
        bill.save()
        item = BillItem(bill=bill, qty=6,
                        sku="SKU45", name="Item",
                        description="Desc", shop=self.shop)
        item.save()
        with self.assertRaises(BillItem.DoesNotExist):
            BillItem.objects.get(pk=item.pk)

    def test_can_edit_item_in_proforma_bill(self):
        """
        Checks that I can add items to a proforma bill
        """
        bill = Bill(shop=self.shop, number=3,
                    issued_to=self.customer, is_proforma=True)
        bill.save()
        item = BillItem(bill=bill, qty=6,
                        sku="SKU45", name="Item",
                        description="Desc", shop=self.shop)
        item.save()
        item.qty = 8
        item.save()
        self.assertEqual(BillItem.objects.get(pk=item.pk).qty, 8)

    def test_bill_item_secret_save(self):
        """
        Checks that I can't add items to a final bill
        """
        bill = Bill(shop=self.shop, number=3,
                    issued_to=self.customer, is_proforma=False)
        bill.save()
        item = BillItem(bill=bill, qty=6,
                        sku="SKU45", name="Item",
                        description="Desc", shop=self.shop)
        item.secret_save()
        self.assertEquals(BillItem.objects.get(pk=item.pk).qty, 6)

    def test_bill_items(self):
        """
        Checks the Bill.items method
        """
        bill = Bill(shop=self.shop, number=3,
                    issued_to=self.customer, is_proforma=True)
        bill.save()
        item = BillItem(bill=bill, qty=6,
                        sku="SKU45", name="Item",
                        description="Desc", shop=self.shop)
        item.save()
        self.assertEqual(bill.items[0], item)


class ShopTests(TestCase):
    """
    Tests that check the Shop model
    """
    def test_Shop_has_all_the_required_fields(self):
        pshop = Shop(name="Tienda 1")
        pshop.save()
        shop = Shop.objects.get(pk=pshop.pk)
        self.assertEquals(shop.name, "Tienda 1")
        pshop.delete()

    def test_Shop_str(self):
        shop = Shop(name="Tienda 1")
        self.assertEquals(str(shop), "Tienda 1")


class ShopUserTests(TestCase):
    """
    Tests that check the ShopUser model
    """
    def setUp(self):
        self.shop = Shop(name="Tienda 1")
        self.shop.save()
        self.user = User(username="Pepe")
        self.user.save()

    def tearDown(self):
        self.shop.delete()
        self.user.delete()

    def test_ShopUser_has_all_the_required_fields(self):
        psu = ShopUser(shop=self.shop, user=self.user)
        psu.save()
        su = ShopUser.objects.get(pk=psu.pk)
        self.assertEquals(su.shop, self.shop)
        self.assertEquals(su.user, self.user)
        psu.delete()

    def test_ShopUser_str(self):
        su = ShopUser(shop=self.shop, user=self.user)
        self.assertEquals(str(su), self.user.username)


class CustomerTests(TestCase):
    """
    Tests that check the Customer model
    """
    def test_Customer_has_all_the_required_fields(self):
        pcust = Customer(name="Pepe")
        pcust.save()
        cust = Customer.objects.get(pk=pcust.pk)
        self.assertEquals(cust.name, "Pepe")
        cust.delete()

    def test_Customer_str(self):
        cust = Customer(name="Pepe")
        self.assertEquals(str(cust), "Pepe")
