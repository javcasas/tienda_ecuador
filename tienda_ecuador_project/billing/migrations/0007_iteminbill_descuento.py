# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('billing', '0006_auto_20151030_1210'),
    ]

    operations = [
        migrations.AddField(
            model_name='iteminbill',
            name='descuento',
            field=models.DecimalField(default=0, max_digits=20, decimal_places=8),
            preserve_default=True,
        ),
    ]
