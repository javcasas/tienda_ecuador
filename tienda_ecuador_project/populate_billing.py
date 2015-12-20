# * encoding: utf-8 *
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE',
                      'tienda_ecuador_project.settings')

import django
django.setup()

from functools import partial
from datetime import datetime, date
from decimal import Decimal

import pytz
from sri import models as sri
from company_accounts import models as company_accounts
from inventory import models as inventory
from billing import models as billing
from django.contrib.auth.models import User


def get_date():
    return datetime.now(tz=pytz.timezone('America/Guayaquil'))


def print_instance(klass, kwargs):
    params = u", ".join([u"{}={}".format(k, v)
                        for (k, v) in kwargs.iteritems()])
    print u"Adding", klass.__name__, params


def add_instance(klass, **kwargs):
    print_instance(klass, kwargs)
    s = klass.objects.update_or_create(**kwargs)[0]
    s.full_clean()
    s.save()
    return s

#add_Company = partial(add_instance, company_accounts.Company)
#add_Item = partial(add_instance, billing.Item)
#add_Customer = partial(add_instance, billing.Customer)
#add_CompanyUser = partial(add_instance, company_accounts.CompanyUser)
#add_ProformaBill = partial(add_instance, billing.Bill)
#add_ProformaBillItem = partial(add_instance, models.BillItem)


def add_User(**kwargs):
    u = add_instance(User, **kwargs)
    u.set_password(kwargs['password'])
    u.save()
    return u


def my_populate():
    u1, created = User.objects.get_or_create(username='javier')
    u1.set_password("tiaputa")
    u1.is_staff = True
    u1.is_superuser = True
    u1.save()

    t1 = add_instance(company_accounts.Company,
                      nombre_comercial=u"DSSTI", ruc=u'1756760292001',
                      razon_social=u'CASAS VELASCO JAVIER',
                      direccion_matriz=u'C/ Francisco de Orellana Oe2-143, Tumbaco, Quito')
    t1.licence.approve("professional", date(2020, 1, 1))
    e1 = add_instance(company_accounts.Establecimiento,
                      company=t1,
                      direccion=t1.direccion_matriz,
                      descripcion='Matriz',
                      codigo='001')
    pe1 = add_instance(company_accounts.PuntoEmision,
                       establecimiento=e1,
                       descripcion='Caja principal',
                       codigo='001')
    cu1 = add_instance(company_accounts.CompanyUser,
                       user=u1, company=t1)

    u2, created = User.objects.get_or_create(username='test')
    u2.set_password("test")
    u2.save()

    t2 = add_instance(company_accounts.Company,
                      nombre_comercial=u"ALMACENES EL FOCO", ruc=u'1111111111001',
                      razon_social=u'ROBERTO GUTIERREZ',
                      direccion_matriz=u'C/ ORELLANA, QUITO')
    e2 = add_instance(company_accounts.Establecimiento,
                      company=t2,
                      direccion=t2.direccion_matriz,
                      descripcion='Matriz',
                      codigo='001')
    pe2 = add_instance(company_accounts.PuntoEmision,
                       establecimiento=e2,
                       descripcion='Caja principal',
                       codigo='001')
    cu2 = add_instance(company_accounts.CompanyUser,
                       user=u2, company=t2)

    #i1 = add_instance(billing.Item,
    #    sku=u'H1',
    #    name=u'Consultoría 1 hora',
    #    description=u'1 Hora de servicios de consultoría',
    #    unit_cost=Decimal(10),
    #    unit_price=Decimal(35),
    #    tipo='servicio',
    #    company=t1,
    #    decimales_qty=0)
    #i1.tax_items.add(models.Iva.objects.get(porcentaje=Decimal(12)))

    return locals()


if __name__ == '__main__':
    import load_fixtures
    load_fixtures.main()
    print "Starting Billing population script..."
    my_populate()
