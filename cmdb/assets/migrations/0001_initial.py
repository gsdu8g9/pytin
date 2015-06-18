# -*- coding: utf-8 -*-
from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('resources', '0001_initial'),
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
            bases=('resources.resource',),
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
