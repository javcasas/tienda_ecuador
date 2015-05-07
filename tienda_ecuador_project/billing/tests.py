from django.test import TestCase
from billing.models import Bill, Shop, Customer, BillItem

# Create your tests here.
class BillTests(TestCase):
    """
    Tests that check the Bill model
    """
    def setUp(self):
        self.shop = Shop(name="Tienda 1")
        self.shop.save()
        self.customer = Customer(name="Pepe")
        self.customer.save()

    def test_bill_can_be_written_if_is_proforma(self):
        """
        Checks that the bill can be written if is proforma
        """
        bill = Bill(shop=self.shop, number=3, issued_to=self.customer, is_proforma=True)
        bill.save()
        self.assertEqual(Bill.objects.get(pk=bill.pk).number, '3')
        bill.number=4
        bill.save()
        self.assertEqual(Bill.objects.get(pk=bill.pk).number, '4')

    def test_bill_is_final(self):
        """
        Checks that the bill can only be written if is proforma
        """
        bill = Bill(shop=self.shop, number=3, issued_to=self.customer, is_proforma=True)
        bill.save()
        bill.is_proforma=False
        bill.save()
        bill.number=4
        bill.save()
        self.assertEqual(Bill.objects.get(pk=bill.pk).number, '3')

    def test_bill_secret_save(self):
        """
        Checks Bill.secret_save
        """
        bill = Bill(shop=self.shop, number=5, issued_to=self.customer, is_proforma=False)
        bill.save()
        bill.number=6
        bill.secret_save()
        self.assertEqual(Bill.objects.get(pk=bill.pk).number, '6')

    def test_can_add_item_to_proforma_bill(self):
        """
        Checks that I can add items to a proforma bill
        """
        bill = Bill(shop=self.shop, number=3, issued_to=self.customer, is_proforma=True)
        bill.save()
        item = BillItem(bill=bill, qty=6, sku="SKU45", name="Item", description="Desc", shop=self.shop)
        item.save()
        self.assertEqual(BillItem.objects.get(pk=item.pk).qty, 6)

    def test_cant_add_item_to_final_bill(self):
        """
        Checks that I can't add items to a final bill
        """
        bill = Bill(shop=self.shop, number=3, issued_to=self.customer, is_proforma=False)
        bill.save()
        item = BillItem(bill=bill, qty=6, sku="SKU45", name="Item", description="Desc", shop=self.shop)
        item.save()
        with self.assertRaises(BillItem.DoesNotExist):
            BillItem.objects.get(pk=item.pk)
