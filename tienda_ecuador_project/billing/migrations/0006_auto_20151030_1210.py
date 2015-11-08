# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('billing', '0005_proformabill_issues'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='proformabill',
            name='issues',
        ),
        migrations.AddField(
            model_name='basebill',
            name='issues',
            field=models.TextField(default=b'', blank=True),
            preserve_default=True,
        ),
    ]
