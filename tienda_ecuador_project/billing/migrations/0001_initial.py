# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from decimal import Decimal
import billing.validators
from django.conf import settings
import billing.models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='BaseBill',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('number', models.CharField(max_length=20, blank=True)),
                ('date', models.DateTimeField()),
                ('xml_content', models.TextField()),
                ('ride_content', models.TextField()),
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
                ('tipo_identificacion', models.CharField(max_length=100, validators=[billing.validators.OneOf(b'cedula', b'ruc', b'pasaporte')])),
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
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Bill',
            fields=[
                ('basebill_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='billing.BaseBill')),
            ],
            options={
            },
            bases=(billing.models.ReadOnlyMixin, 'billing.basebill'),
        ),
        migrations.CreateModel(
            name='Company',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('nombre_comercial', models.CharField(unique=True, max_length=100)),
                ('ruc', models.CharField(unique=True, max_length=100)),
                ('razon_social', models.CharField(unique=True, max_length=100)),
                ('direccion_matriz', models.CharField(max_length=100)),
                ('contribuyente_especial', models.CharField(max_length=20, blank=True)),
                ('obligado_contabilidad', models.BooleanField(default=False)),
                ('ambiente_sri', models.CharField(default=b'pruebas', max_length=20, validators=[billing.validators.OneOf(b'pruebas', b'produccion')])),
                ('siguiente_comprobante_pruebas', models.IntegerField(default=1)),
                ('siguiente_comprobante_produccion', models.IntegerField(default=1)),
                ('cert', models.CharField(max_length=20000, blank=True)),
                ('key', models.CharField(max_length=100, blank=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='CompanyUser',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('company', models.ForeignKey(to='billing.Company')),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Customer',
            fields=[
                ('basecustomer_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='billing.BaseCustomer')),
                ('company', models.ForeignKey(to='billing.Company')),
            ],
            options={
            },
            bases=('billing.basecustomer',),
        ),
        migrations.CreateModel(
            name='Establecimiento',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('descripcion', models.CharField(max_length=50)),
                ('codigo', models.CharField(max_length=3)),
                ('direccion', models.CharField(max_length=100)),
                ('company', models.ForeignKey(to='billing.Company')),
            ],
            options={
            },
            bases=(models.Model,),
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
                ('company', models.ForeignKey(to='billing.Company')),
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
                ('cantidad', models.IntegerField()),
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
                ('issued_to', models.ForeignKey(to='billing.Customer')),
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
            name='PuntoEmision',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('descripcion', models.CharField(max_length=50)),
                ('codigo', models.CharField(max_length=3)),
                ('establecimiento', models.ForeignKey(to='billing.Establecimiento')),
            ],
            options={
            },
            bases=(models.Model,),
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
                ('grupo', models.IntegerField()),
            ],
            options={
            },
            bases=('billing.tax',),
        ),
        migrations.AddField(
            model_name='proformabill',
            name='punto_emision',
            field=models.ForeignKey(to='billing.PuntoEmision'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='pago',
            name='bill',
            field=models.ForeignKey(to='billing.BaseBill'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='pago',
            name='forma_pago',
            field=models.ForeignKey(to='billing.FormaPago'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='pago',
            name='plazo_pago',
            field=models.ForeignKey(to='billing.PlazoPago'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='bill',
            name='company',
            field=models.ForeignKey(to='billing.Company'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='baseitem',
            name='tax_items',
            field=models.ManyToManyField(to='billing.Tax'),
            preserve_default=True,
        ),
    ]
