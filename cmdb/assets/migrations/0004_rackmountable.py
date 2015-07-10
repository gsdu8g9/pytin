# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('assets', '0003_datacenter'),
    ]

    operations = [
        migrations.CreateModel(
            name='RackMountable',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('assets.assetresource',),
        ),
    ]
