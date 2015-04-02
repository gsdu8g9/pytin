# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('resources', '0015_auto_20150324_1714'),
    ]

    operations = [
        migrations.CreateModel(
            name='ResourcePool',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('resources.resource',),
        ),
        migrations.AlterField(
            model_name='resource',
            name='created_at',
            field=models.DateTimeField(default=datetime.datetime(2015, 4, 2, 22, 27, 51, 456698, tzinfo=utc), verbose_name=b'Date created', db_index=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='resource',
            name='type',
            field=models.CharField(max_length=155, db_index=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='resourceoption',
            name='format',
            field=models.CharField(default=b'string', max_length=25, db_index=True, choices=[(b'dict', b'Dictionary string'), (b'int', b'Integer value'), (b'float', b'Float value'), (b'string', b'String value')]),
            preserve_default=True,
        ),
    ]
