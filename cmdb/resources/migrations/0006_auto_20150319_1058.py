# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('resources', '0005_auto_20150319_1053'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='resource',
            name='created_date',
        ),
        migrations.AddField(
            model_name='resource',
            name='created_at',
            field=models.DateTimeField(default=datetime.datetime(2015, 3, 19, 10, 58, 34, 338618, tzinfo=utc), auto_now_add=True, verbose_name=b'date created', db_index=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='resource',
            name='updated_at',
            field=models.DateTimeField(default=datetime.datetime(2015, 3, 19, 10, 58, 43, 682115, tzinfo=utc), auto_now=True, verbose_name=b'date updated', db_index=True),
            preserve_default=False,
        ),
    ]
