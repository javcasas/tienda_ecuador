from django.contrib import admin
import models

# Register your models here.
admin.site.register(models.Company)
admin.site.register(models.CompanyUser)
admin.site.register(models.Establecimiento)
admin.site.register(models.PuntoEmision)


class LicenceAdmin(admin.ModelAdmin):
    list_display = ('licence', 'expiration', 'company', 'next_licence')

admin.site.register(models.Licence, LicenceAdmin)


class BannedCompanyAdmin(admin.ModelAdmin):
    list_display = ('ruc', 'reason')

admin.site.register(models.BannedCompany, BannedCompanyAdmin)


class LicenceHistoryAdmin(admin.ModelAdmin):
    list_display = ('licence', 'company_ruc', 'date', 'action')
    list_filter = ('licence__company',)
    def company_ruc(self, ob):
        return u"{} - {}".format(ob.company.ruc, ob.company.razon_social)
    #company_ruc.admin_order_field = 'licence__company'
    

admin.site.register(models.LicenceHistory, LicenceHistoryAdmin)


class LicenceUpdateRequestAdmin(admin.ModelAdmin):
    list_display = ('licence', 'date', 'action', 'result')
    list_filter = ('licence__company', 'licence__company__ruc',)
    date_hierarchy = 'date'

admin.site.register(models.LicenceUpdateRequest, LicenceUpdateRequestAdmin)
