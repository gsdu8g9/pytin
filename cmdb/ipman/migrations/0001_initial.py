# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('resources', '0017_auto_20150410_1804'),
    ]

    operations = [
        migrations.CreateModel(
            name='IPAddress',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('resources.resource',),
        ),
        migrations.CreateModel(
            name='IPAddressPool',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('resources.resourcepool',),
        ),
        migrations.CreateModel(
            name='IPAddressRangePool',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('ipman.ipaddresspool',),
        ),
        migrations.CreateModel(
            name='IPNetworkPool',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('ipman.ipaddresspool',),
        ),
    ]
