# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('resources', '0013_auto_20150323_1523'),
    ]

    operations = [
        migrations.AlterField(
            model_name='resource',
            name='created_at',
            field=models.DateTimeField(default=datetime.datetime(2015, 3, 23, 13, 30, 22, 158849, tzinfo=utc), verbose_name=b'Date created', db_index=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='resourceoption',
            name='namespace',
            field=models.CharField(default=b'', max_length=155, db_index=True),
            preserve_default=True,
        ),
    ]
