# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from decimal import Decimal
import billing.models


class Migration(migrations.Migration):

    dependencies = [
        ('company_accounts', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='BaseBill',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('number', models.CharField(max_length=20, blank=True)),
                ('date', models.DateTimeField()),
                ('xml_content', models.TextField(blank=True)),
                ('ride_content', models.TextField(blank=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='BaseCustomer',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('razon_social', models.CharField(max_length=100)),
                ('tipo_identificacion', models.CharField(max_length=100, choices=[(b'cedula', b'C\xc3\xa9dula'), (b'ruc', b'RUC'), (b'pasaporte', b'Pasaporte')])),
                ('identificacion', models.CharField(max_length=100)),
                ('email', models.CharField(max_length=100, blank=True)),
                ('direccion', models.CharField(max_length=100, blank=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='BaseItem',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('sku', models.CharField(max_length=50)),
                ('name', models.CharField(max_length=50)),
                ('description', models.CharField(max_length=500)),
                ('unit_cost', models.DecimalField(max_digits=20, decimal_places=8)),
                ('unit_price', models.DecimalField(max_digits=20, decimal_places=8)),
                ('tipo', models.CharField(max_length=10, choices=[(b'producto', b'Producto'), (b'servicio', b'Servicio')])),
                ('decimales_qty', models.IntegerField(default=0, max_length=1, choices=[(0, b'Unidades Enteras'), (1, b'1 Decimal'), (2, b'2 Decimales'), (3, b'3 Decimales')])),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Bill',
            fields=[
                ('basebill_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='billing.BaseBill')),
                ('company', models.ForeignKey(to='company_accounts.Company')),
            ],
            options={
            },
            bases=(billing.models.ReadOnlyMixin, 'billing.basebill'),
        ),
        migrations.CreateModel(
            name='Customer',
            fields=[
                ('basecustomer_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='billing.BaseCustomer')),
                ('company', models.ForeignKey(to='company_accounts.Company')),
            ],
            options={
            },
            bases=('billing.basecustomer',),
        ),
        migrations.CreateModel(
            name='FormaPago',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('codigo', models.CharField(max_length=2)),
                ('descripcion', models.CharField(max_length=50)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Item',
            fields=[
                ('baseitem_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='billing.BaseItem')),
                ('company', models.ForeignKey(to='company_accounts.Company')),
            ],
            options={
            },
            bases=('billing.baseitem',),
        ),
        migrations.CreateModel(
            name='ItemInBill',
            fields=[
                ('baseitem_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='billing.BaseItem')),
                ('qty', models.DecimalField(max_digits=20, decimal_places=8)),
            ],
            options={
            },
            bases=('billing.baseitem',),
        ),
        migrations.CreateModel(
            name='Pago',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('porcentaje', models.DecimalField(max_digits=20, decimal_places=8)),
                ('forma_pago', models.ForeignKey(to='billing.FormaPago')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='PlazoPago',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('descripcion', models.CharField(max_length=50)),
                ('unidad_tiempo', models.CharField(max_length=20)),
                ('tiempo', models.IntegerField()),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ProformaBill',
            fields=[
                ('basebill_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='billing.BaseBill')),
                ('secuencial_pruebas', models.IntegerField(default=0, blank=True)),
                ('secuencial_produccion', models.IntegerField(default=0, blank=True)),
                ('issued_to', models.ForeignKey(blank=True, to='billing.Customer', null=True)),
                ('punto_emision', models.ForeignKey(to='company_accounts.PuntoEmision')),
            ],
            options={
            },
            bases=('billing.basebill',),
        ),
        migrations.CreateModel(
            name='ProformaBillItem',
            fields=[
                ('iteminbill_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='billing.ItemInBill')),
                ('proforma_bill', models.ForeignKey(to='billing.ProformaBill')),
            ],
            options={
            },
            bases=('billing.iteminbill',),
        ),
        migrations.CreateModel(
            name='Tax',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('descripcion', models.CharField(max_length=100)),
                ('codigo', models.CharField(max_length=10)),
                ('porcentaje', models.DecimalField(max_digits=6, decimal_places=2)),
                ('valor_fijo', models.DecimalField(default=Decimal('0.00'), max_digits=6, decimal_places=2)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Iva',
            fields=[
                ('tax_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='billing.Tax')),
            ],
            options={
            },
            bases=('billing.tax',),
        ),
        migrations.CreateModel(
            name='Ice',
            fields=[
                ('tax_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='billing.Tax')),
            ],
            options={
            },
            bases=('billing.tax',),
        ),
        migrations.AddField(
            model_name='pago',
            name='plazo_pago',
            field=models.ForeignKey(to='billing.PlazoPago'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='pago',
            name='proforma_bill',
            field=models.ForeignKey(to='billing.ProformaBill'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='baseitem',
            name='tax_items',
            field=models.ManyToManyField(to='billing.Tax'),
            preserve_default=True,
        ),
    ]
