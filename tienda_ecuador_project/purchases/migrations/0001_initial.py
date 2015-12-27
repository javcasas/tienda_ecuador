# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime


class Migration(migrations.Migration):

    dependencies = [
        ('stakeholders', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Purchase',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('date', models.DateField(default=datetime.date.today)),
                ('xml_content', models.TextField()),
                ('closed', models.BooleanField(default=False)),
                ('comment', models.TextField(blank=True)),
                ('number', models.CharField(max_length=20, blank=True)),
                ('seller', models.ForeignKey(to='stakeholders.Seller')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
