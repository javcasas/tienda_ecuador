from django.contrib import admin
from models import (Item, Bill, Customer, Company, CompanyUser,
                    ProformaBill, ProformaBillItem)
import models

# Register your models here.
admin.site.register(Company)
admin.site.register(CompanyUser)
admin.site.register(Item)
admin.site.register(Customer)
admin.site.register(Bill)
admin.site.register(ProformaBillItem)
admin.site.register(ProformaBill)
admin.site.register(models.Pago)
