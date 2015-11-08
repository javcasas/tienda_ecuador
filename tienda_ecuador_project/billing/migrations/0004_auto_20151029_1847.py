# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('billing', '0003_auto_20151029_1752'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='proformabill',
            name='clave_acceso',
        ),
        migrations.AddField(
            model_name='basebill',
            name='clave_acceso',
            field=models.CharField(max_length=50, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='bill',
            name='iva',
            field=models.DecimalField(default=0, max_digits=20, decimal_places=8),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='bill',
            name='iva_retenido',
            field=models.DecimalField(default=0, max_digits=20, decimal_places=8),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='bill',
            name='total_sin_iva',
            field=models.DecimalField(default=0, max_digits=20, decimal_places=8),
            preserve_default=False,
        ),
    ]
