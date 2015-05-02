# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('billing', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ShopUser',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('shop', models.ForeignKey(to='billing.Shop')),
                ('user', models.OneToOneField(to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AlterField(
            model_name='bill',
            name='issued_to',
            field=models.ForeignKey(to='billing.Customer', blank=True),
        ),
        migrations.AlterField(
            model_name='bill',
            name='number',
            field=models.CharField(max_length=20, blank=True),
        ),
    ]
