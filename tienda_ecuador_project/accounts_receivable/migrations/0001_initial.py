# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('billing', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Payment',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('date', models.DateField()),
                ('qty', models.DecimalField(max_digits=20, decimal_places=8)),
                ('comment', models.TextField(blank=True)),
                ('method', models.ForeignKey(to='billing.FormaPago')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Receivable',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('qty', models.DecimalField(max_digits=20, decimal_places=8)),
                ('date', models.DateField()),
                ('received', models.BooleanField(default=False)),
                ('comment', models.TextField(blank=True)),
                ('bill', models.ForeignKey(to='billing.Bill')),
                ('method', models.ForeignKey(to='billing.FormaPago')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='payment',
            name='receivable',
            field=models.ForeignKey(to='accounts_receivable.Receivable'),
            preserve_default=True,
        ),
    ]
