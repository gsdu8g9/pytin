# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('resources', '0009_auto_20150319_2341'),
    ]

    operations = [
        migrations.AlterField(
            model_name='resource',
            name='created_at',
            field=models.DateTimeField(default=datetime.datetime(2015, 3, 19, 20, 42, 16, 342121, tzinfo=utc), verbose_name=b'Date created', db_index=True),
            preserve_default=True,
        ),
    ]
