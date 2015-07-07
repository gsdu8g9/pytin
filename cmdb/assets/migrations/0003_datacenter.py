# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('resources', '0009_auto_20150616_1319'),
        ('assets', '0002_auto_20150623_1703'),
    ]

    operations = [
        migrations.CreateModel(
            name='Datacenter',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('resources.resource',),
        ),
    ]
