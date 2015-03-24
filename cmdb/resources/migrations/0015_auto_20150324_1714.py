# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('resources', '0014_auto_20150323_1630'),
    ]

    operations = [
        migrations.AlterField(
            model_name='resource',
            name='created_at',
            field=models.DateTimeField(default=datetime.datetime(2015, 3, 24, 14, 13, 59, 940476, tzinfo=utc), verbose_name=b'Date created', db_index=True),
            preserve_default=True,
        ),
    ]
