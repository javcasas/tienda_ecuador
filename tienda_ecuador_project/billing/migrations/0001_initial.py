# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
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
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='BaseCustomer',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=100)),
                ('sri_ruc', models.CharField(max_length=100)),
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
                ('vat_percent', models.IntegerField()),
                ('unit_cost', models.DecimalField(max_digits=20, decimal_places=8)),
                ('unit_price', models.DecimalField(max_digits=20, decimal_places=8)),
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
            name='BillCustomer',
            fields=[
                ('basecustomer_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='billing.BaseCustomer')),
            ],
            options={
            },
            bases=(billing.models.ReadOnlyMixin, 'billing.basecustomer'),
        ),
        migrations.CreateModel(
            name='BillItem',
            fields=[
                ('baseitem_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='billing.BaseItem')),
                ('qty', models.DecimalField(max_digits=20, decimal_places=8)),
                ('bill', models.ForeignKey(to='billing.Bill')),
            ],
            options={
            },
            bases=(billing.models.ReadOnlyMixin, 'billing.baseitem'),
        ),
        migrations.CreateModel(
            name='Company',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=100)),
                ('sri_ruc', models.CharField(unique=True, max_length=100)),
                ('sri_razon_social', models.CharField(unique=True, max_length=100)),
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
                ('baseitem_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='billing.BaseItem')),
                ('qty', models.DecimalField(max_digits=20, decimal_places=8)),
                ('proforma_bill', models.ForeignKey(to='billing.ProformaBill')),
            ],
            options={
            },
            bases=('billing.baseitem',),
        ),
        migrations.AddField(
            model_name='bill',
            name='issued_to',
            field=models.ForeignKey(to='billing.BillCustomer'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='basebill',
            name='company',
            field=models.ForeignKey(to='billing.Company'),
            preserve_default=True,
        ),
    ]
