# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('resources', '0017_auto_20150410_1804'),
    ]

    operations = [
        migrations.CreateModel(
            name='InventoryResource',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('resources.resource',),
        ),
        migrations.CreateModel(
            name='PortResource',
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
            bases=('resources.resourcepool',),
        ),
        migrations.CreateModel(
            name='RackResource',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('assets.inventoryresource',),
        ),
        migrations.CreateModel(
            name='ServerResource',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('assets.inventoryresource',),
        ),
    ]
