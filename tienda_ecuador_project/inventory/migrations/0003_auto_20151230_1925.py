# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('purchases', '0001_initial'),
        ('inventory', '0002_item_distributor_code'),
    ]

    operations = [
        migrations.AddField(
            model_name='batch',
            name='purchase',
            field=models.ForeignKey(blank=True, to='purchases.Purchase', null=True),
        ),
        migrations.AlterField(
            model_name='item',
            name='decimales_qty',
            field=models.IntegerField(default=0, choices=[(0, b'Unidades Enteras'), (1, b'1 Decimal'), (2, b'2 Decimales'), (3, b'3 Decimales')]),
        ),
    ]
