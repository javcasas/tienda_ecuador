# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('company_accounts', '0001_initial'),
        ('sri', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Batch',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('unit_cost', models.DecimalField(max_digits=20, decimal_places=8)),
                ('code', models.CharField(max_length=50)),
                ('acquisition_date', models.DateField()),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Item',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=50)),
                ('code', models.CharField(max_length=50)),
                ('description', models.CharField(max_length=500, blank=True)),
                ('tipo', models.CharField(max_length=10, choices=[(b'producto', b'Producto'), (b'servicio', b'Servicio')])),
                ('decimales_qty', models.IntegerField(default=0, max_length=1, choices=[(0, b'Unidades Enteras'), (1, b'1 Decimal'), (2, b'2 Decimales'), (3, b'3 Decimales')])),
                ('company', models.ForeignKey(to='company_accounts.Company')),
                ('tax_items', models.ManyToManyField(to='sri.Tax')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='SKU',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('qty', models.DecimalField(max_digits=20, decimal_places=8)),
                ('unit_price', models.DecimalField(max_digits=20, decimal_places=8)),
                ('location', models.CharField(max_length=500)),
                ('batch', models.ForeignKey(to='inventory.Batch')),
                ('establecimiento', models.ForeignKey(to='company_accounts.Establecimiento')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='batch',
            name='item',
            field=models.ForeignKey(to='inventory.Item'),
            preserve_default=True,
        ),
    ]
