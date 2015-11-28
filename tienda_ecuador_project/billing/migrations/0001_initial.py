# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from decimal import Decimal


class Migration(migrations.Migration):

    dependencies = [
        ('company_accounts', '0001_initial'),
    ]

    operations = [
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
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('xml_content', models.TextField(blank=True)),
                ('clave_acceso', models.CharField(default=b'', max_length=50, blank=True)),
                ('numero_autorizacion', models.CharField(default=b'', max_length=50, blank=True)),
                ('fecha_autorizacion', models.DateTimeField(null=True, blank=True)),
                ('issues', models.TextField(default=b'', blank=True)),
                ('ambiente_sri', models.CharField(max_length=20, choices=[(b'pruebas', b'Pruebas'), (b'produccion', b'Producci\xc3\xb3n')])),
                ('status', models.CharField(default=b'NotSent', max_length=20, choices=[(b'NotSent', b'No enviado al SRI'), (b'ReadyToSend', b'Enviando al SRI'), (b'Sent', b'Enviada al SRI'), (b'Accepted', b'Aceptada por el SRI')])),
                ('number', models.CharField(max_length=20, blank=True)),
                ('date', models.DateTimeField()),
                ('secuencial', models.IntegerField(default=0, blank=True)),
                ('company', models.ForeignKey(to='company_accounts.Company')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='BillItem',
            fields=[
                ('baseitem_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='billing.BaseItem')),
                ('qty', models.DecimalField(max_digits=20, decimal_places=8)),
                ('descuento', models.DecimalField(default=0, max_digits=20, decimal_places=8)),
                ('bill', models.ForeignKey(to='billing.Bill')),
            ],
            options={
            },
            bases=('billing.baseitem',),
        ),
        migrations.CreateModel(
            name='Customer',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('razon_social', models.CharField(max_length=100)),
                ('tipo_identificacion', models.CharField(max_length=100, choices=[(b'cedula', b'C\xc3\xa9dula'), (b'ruc', b'RUC'), (b'pasaporte', b'Pasaporte')])),
                ('identificacion', models.CharField(max_length=100)),
                ('email', models.CharField(max_length=100, blank=True)),
                ('direccion', models.CharField(max_length=100, blank=True)),
                ('company', models.ForeignKey(to='company_accounts.Company')),
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
                ('company', models.ForeignKey(to='company_accounts.Company')),
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
                ('bill', models.ForeignKey(to='billing.Bill')),
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
            model_name='bill',
            name='issued_to',
            field=models.ForeignKey(blank=True, to='billing.Customer', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='bill',
            name='punto_emision',
            field=models.ForeignKey(blank=True, to='company_accounts.PuntoEmision', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='baseitem',
            name='tax_items',
            field=models.ManyToManyField(to='billing.Tax'),
            preserve_default=True,
        ),
    ]
