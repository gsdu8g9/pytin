# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('assets', '0002_auto_20150520_1324'),
    ]

    operations = [
        migrations.CreateModel(
            name='GatewaySwitch',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('assets.inventoryresource',),
        ),
        migrations.CreateModel(
            name='Switch',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('assets.inventoryresource',),
        ),
    ]
