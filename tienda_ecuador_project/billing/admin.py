from django.contrib import admin
from models import Shop, Item, Bill, BillItem, Customer

# Register your models here.
admin.site.register(Shop)
admin.site.register(Item)
admin.site.register(Customer)
admin.site.register(Bill)
admin.site.register(BillItem)
