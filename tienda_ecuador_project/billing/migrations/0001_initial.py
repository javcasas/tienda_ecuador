# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='BaseItem',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('sku', models.CharField(max_length=50)),
                ('name', models.CharField(max_length=50)),
                ('description', models.CharField(max_length=500)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Bill',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('number', models.CharField(max_length=20, blank=True)),
                ('is_proforma', models.BooleanField(default=False)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='BillItem',
            fields=[
                ('baseitem_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='billing.BaseItem')),
                ('qty', models.IntegerField()),
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
                ('name', models.CharField(max_length=100)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Item',
            fields=[
                ('baseitem_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='billing.BaseItem')),
            ],
            options={
            },
            bases=('billing.baseitem',),
        ),
        migrations.CreateModel(
            name='Shop',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=100)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ShopUser',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('shop', models.ForeignKey(to='billing.Shop')),
                ('user', models.OneToOneField(to=settings.AUTH_USER_MODEL)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='bill',
            name='issued_to',
            field=models.ForeignKey(to='billing.Customer', blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='bill',
            name='shop',
            field=models.ForeignKey(to='billing.Shop'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='baseitem',
            name='shop',
            field=models.ForeignKey(to='billing.Shop'),
            preserve_default=True,
        ),
    ]
