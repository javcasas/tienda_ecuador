# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('customer_accounts', '0001_initial'),
        ('inventory', '0001_initial'),
        ('company_accounts', '0001_initial'),
    ]

    operations = [
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
                ('status', models.CharField(default=b'NotSent', max_length=20, choices=[(b'NotSent', b'No enviado al SRI'), (b'ReadyToSend', b'Enviando al SRI'), (b'Sent', b'Enviada al SRI'), (b'Accepted', b'Aceptada por el SRI'), (b'Annulled', b'Anulado')])),
                ('sri_last_check', models.DateTimeField(null=True, blank=True)),
                ('number', models.CharField(max_length=20, blank=True)),
                ('date', models.DateTimeField()),
                ('secuencial', models.IntegerField(default=0, blank=True)),
                ('company', models.ForeignKey(to='company_accounts.Company')),
                ('issued_to', models.ForeignKey(blank=True, to='customer_accounts.Customer', null=True)),
                ('punto_emision', models.ForeignKey(blank=True, to='company_accounts.PuntoEmision', null=True)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='BillItem',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('qty', models.DecimalField(max_digits=20, decimal_places=8)),
                ('descuento', models.DecimalField(default=0, max_digits=20, decimal_places=8)),
                ('bill', models.ForeignKey(to='billing.Bill')),
                ('sku', models.ForeignKey(to='inventory.SKU')),
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
        migrations.AddField(
            model_name='pago',
            name='plazo_pago',
            field=models.ForeignKey(to='billing.PlazoPago'),
            preserve_default=True,
        ),
    ]
