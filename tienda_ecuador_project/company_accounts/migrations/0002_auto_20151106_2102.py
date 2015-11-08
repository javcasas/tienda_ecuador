# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import company_accounts.models


class Migration(migrations.Migration):

    dependencies = [
        ('company_accounts', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='company',
            name='logo',
            field=models.ImageField(storage=company_accounts.models.OverwritingStorage(), upload_to=company_accounts.models.logo_path_generator, blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='company',
            name='nombre_comercial',
            field=models.CharField(max_length=100),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='company',
            name='razon_social',
            field=models.CharField(max_length=100),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='company',
            name='ruc',
            field=models.CharField(max_length=100),
            preserve_default=True,
        ),
    ]
