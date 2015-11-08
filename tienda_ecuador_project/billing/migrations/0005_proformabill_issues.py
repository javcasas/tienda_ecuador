# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('billing', '0004_auto_20151029_1847'),
    ]

    operations = [
        migrations.AddField(
            model_name='proformabill',
            name='issues',
            field=models.TextField(default=b'', blank=True),
            preserve_default=True,
        ),
    ]
