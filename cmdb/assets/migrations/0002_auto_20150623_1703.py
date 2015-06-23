# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import assets.models


class Migration(migrations.Migration):

    dependencies = [
        ('resources', '0009_auto_20150616_1319'),
        ('assets', '0001_initial'),
    ]

    operations = [
        migrations.DeleteModel(
            name='InventoryResource',
        ),
        migrations.DeleteModel(
            name='PortResource',
        ),
        migrations.DeleteModel(
            name='RackResource',
        ),
        migrations.DeleteModel(
            name='ServerResource',
        ),
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
            name='PortConnection',
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
            bases=(assets.models.PhysicalAssetMixin, 'assets.assetresource'),
        ),
        migrations.CreateModel(
            name='Server',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=(assets.models.PhysicalAssetMixin, 'assets.assetresource'),
        ),
        migrations.CreateModel(
            name='ServerPort',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=(assets.models.PhysicalAssetMixin, 'assets.networkport'),
        ),
        migrations.CreateModel(
            name='Switch',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=(assets.models.PhysicalAssetMixin, 'assets.assetresource'),
        ),
        migrations.CreateModel(
            name='SwitchPort',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=(assets.models.PhysicalAssetMixin, 'assets.networkport'),
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
            name='GatewaySwitch',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('assets.switch',),
        ),
    ]
