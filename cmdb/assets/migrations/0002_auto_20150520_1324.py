# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('resources', '0003_resource_type'),
        ('assets', '0001_initial'),
    ]

    operations = [
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
            bases=('assets.inventoryresource',),
        ),
        migrations.CreateModel(
            name='Server',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('assets.inventoryresource',),
        ),
        migrations.CreateModel(
            name='ServerPort',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('resources.resource',),
        ),
        migrations.CreateModel(
            name='SwitchPort',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('resources.resource',),
        ),
        migrations.CreateModel(
            name='VirtualServer',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('assets.inventoryresource',),
        ),
    ]
