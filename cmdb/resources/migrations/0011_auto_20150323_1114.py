# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('resources', '0010_auto_20150319_2342'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='resource',
            name='name',
        ),
        migrations.AddField(
            model_name='resource',
            name='status',
            field=models.CharField(default=datetime.datetime(2015, 3, 23, 8, 14, 18, 911584, tzinfo=utc), max_length=25, db_index=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='resource',
            name='type',
            field=models.CharField(default=b'generic', max_length=155, db_index=True, choices=[(b'generic', b'Generic resource')]),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='resourceoption',
            name='format',
            field=models.CharField(default=b'string', max_length=25, db_index=True, choices=[(b'json', b'JSON string'), (b'int', b'Integer value'), (b'float', b'Float value'), (b'string', b'String value')]),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='resource',
            name='created_at',
            field=models.DateTimeField(default=datetime.datetime(2015, 3, 23, 8, 13, 59, 57284, tzinfo=utc), verbose_name=b'Date created', db_index=True),
            preserve_default=True,
        ),
    ]
