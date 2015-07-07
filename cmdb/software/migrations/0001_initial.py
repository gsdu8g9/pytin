# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import assets.models


class Migration(migrations.Migration):

    dependencies = [
        ('resources', '0009_auto_20150616_1319'),
    ]

    operations = [
        migrations.CreateModel(
            name='DirectAdminLicense',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=(assets.models.PhysicalAssetMixin, 'resources.resource'),
        ),
        migrations.CreateModel(
            name='DirectAdminLicensePool',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=(assets.models.PhysicalAssetMixin, 'resources.resource'),
        ),
    ]
