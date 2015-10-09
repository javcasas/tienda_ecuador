from django.contrib import admin
import models

# Register your models here.
admin.site.register(models.Item)
admin.site.register(models.Customer)
admin.site.register(models.Bill)
admin.site.register(models.ProformaBillItem)
admin.site.register(models.ProformaBill)
admin.site.register(models.Pago)
