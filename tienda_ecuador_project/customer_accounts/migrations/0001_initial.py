# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('company_accounts', '0001_initial'),
    ]

    operations = [
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
    ]
