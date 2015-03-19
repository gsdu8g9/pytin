# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('resources', '0006_auto_20150319_1058'),
    ]

    operations = [
        migrations.AlterField(
            model_name='resource',
            name='created_at',
            field=models.DateTimeField(default=datetime.datetime(2015, 3, 19, 11, 3, 33, 945734, tzinfo=utc), verbose_name=b'date created', db_index=True),
            preserve_default=True,
        ),
    ]
