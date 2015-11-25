# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime
from django.conf import settings
import company_accounts.models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Company',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('nombre_comercial', models.CharField(max_length=100)),
                ('ruc', models.CharField(max_length=100)),
                ('razon_social', models.CharField(max_length=100)),
                ('direccion_matriz', models.CharField(max_length=100)),
                ('contribuyente_especial', models.CharField(max_length=20, blank=True)),
                ('obligado_contabilidad', models.BooleanField(default=False)),
                ('siguiente_numero_proforma', models.IntegerField(default=1)),
                ('logo', models.ImageField(storage=company_accounts.models.OverwritingStorage(), upload_to=company_accounts.models.logo_path_generator, blank=True)),
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
                ('company', models.ForeignKey(to='company_accounts.Company')),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Establecimiento',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('descripcion', models.CharField(max_length=50)),
                ('codigo', models.CharField(max_length=3)),
                ('direccion', models.CharField(max_length=100)),
                ('company', models.ForeignKey(to='company_accounts.Company')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Licence',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('licence', models.CharField(default=b'demo', max_length=20, choices=[(b'demo', b'Demo'), (b'basic', b'Basic'), (b'professional', b'Professional'), (b'enterprise', b'Enterprise')])),
                ('expiration', models.DateField(default=datetime.date(2010, 1, 1))),
                ('next_licence', models.CharField(default=b'demo', max_length=20, choices=[(b'demo', b'Demo'), (b'basic', b'Basic'), (b'professional', b'Professional'), (b'enterprise', b'Enterprise')])),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='PuntoEmision',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('descripcion', models.CharField(max_length=50)),
                ('codigo', models.CharField(max_length=3)),
                ('siguiente_secuencial_pruebas', models.IntegerField(default=1)),
                ('siguiente_secuencial_produccion', models.IntegerField(default=1)),
                ('ambiente_sri', models.CharField(default=b'pruebas', max_length=20, choices=[(b'pruebas', b'Pruebas'), (b'produccion', b'Producci\xc3\xb3n')])),
                ('establecimiento', models.ForeignKey(to='company_accounts.Establecimiento')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='company',
            name='licence',
            field=models.ForeignKey(default=company_accounts.models.default_licence, to='company_accounts.Licence'),
            preserve_default=True,
        ),
    ]
