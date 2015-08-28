# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('resources', '0010_auto_20150716_1529'),
    ]

    operations = [
        migrations.CreateModel(
            name='DirectAdminLicense',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('resources.resource',),
        ),
    ]
