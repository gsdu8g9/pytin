# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('resources', '0009_auto_20150616_1319'),
        ('assets', '0003_gatewayswitch_switch'),
    ]
    operations = [
        migrations.CreateModel(
            name='AssetResource',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('resources.resource',),
        ),
        migrations.CreateModel(
            name='NetworkPort',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('resources.resource',),
        ),
        migrations.CreateModel(
            name='VirtualServerPort',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('assets.networkport',),
        ),
    ]

