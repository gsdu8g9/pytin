# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('resources', '0008_auto_20150319_1849'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='resourcehistory',
            name='resource',
        ),
        migrations.DeleteModel(
            name='ResourceHistory',
        ),
        migrations.AlterField(
            model_name='resource',
            name='created_at',
            field=models.DateTimeField(default=datetime.datetime(2015, 3, 19, 20, 41, 48, 149261, tzinfo=utc), verbose_name=b'Date created', db_index=True),
            preserve_default=True,
        ),
        migrations.AlterModelTable(
            name='resource',
            table='resources',
        ),
        migrations.AlterModelTable(
            name='resourceoption',
            table='resource_options',
        ),
    ]
