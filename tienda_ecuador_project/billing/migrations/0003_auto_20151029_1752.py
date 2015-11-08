# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('billing', '0002_proformabill_clave_acceso'),
    ]

    operations = [
        migrations.AlterField(
            model_name='proformabill',
            name='clave_acceso',
            field=models.CharField(max_length=50, blank=True),
            preserve_default=True,
        ),
    ]
