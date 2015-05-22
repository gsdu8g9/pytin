# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime


class Migration(migrations.Migration):

    dependencies = [
        ('resources', '0003_resource_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='resource',
            name='last_seen',
            field=models.DateTimeField(default=datetime.datetime(2015, 5, 22, 11, 48, 48, 216791), verbose_name=b'Date last seen', db_index=True),
        ),
    ]
