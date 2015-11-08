# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('billing', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='proformabill',
            name='clave_acceso',
            field=models.IntegerField(default=0, blank=True),
            preserve_default=True,
        ),
    ]
