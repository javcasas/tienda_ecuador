# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from decimal import Decimal


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
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
                ('tax_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='sri.Tax')),
            ],
            options={
            },
            bases=('sri.tax',),
        ),
        migrations.CreateModel(
            name='Ice',
            fields=[
                ('tax_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='sri.Tax')),
            ],
            options={
            },
            bases=('sri.tax',),
        ),
    ]
