from django.contrib import admin
from models import (Item, Bill, BillItem, Customer, Company, CompanyUser,
                    ProformaBill, ProformaBillItem)

# Register your models here.
admin.site.register(Company)
admin.site.register(CompanyUser)
admin.site.register(Item)
admin.site.register(Customer)
admin.site.register(Bill)
admin.site.register(BillItem)
admin.site.register(ProformaBillItem)
admin.site.register(ProformaBill)
