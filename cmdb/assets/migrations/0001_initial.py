# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('resources', '0010_auto_20150716_1529'),
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
            name='Datacenter',
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
            name='PortConnection',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('resources.resource',),
        ),
        migrations.CreateModel(
            name='RegionResource',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('resources.resource',),
        ),
        migrations.CreateModel(
            name='Rack',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('assets.assetresource',),
        ),
        migrations.CreateModel(
            name='RackMountable',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('assets.assetresource',),
        ),
        migrations.CreateModel(
            name='ServerPort',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('assets.networkport',),
        ),
        migrations.CreateModel(
            name='SwitchPort',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('assets.networkport',),
        ),
        migrations.CreateModel(
            name='VirtualServer',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('assets.assetresource',),
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
        migrations.CreateModel(
            name='Server',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('assets.rackmountable',),
        ),
        migrations.CreateModel(
            name='Switch',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('assets.rackmountable',),
        ),
        migrations.CreateModel(
            name='GatewaySwitch',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('assets.switch',),
        ),
    ]
