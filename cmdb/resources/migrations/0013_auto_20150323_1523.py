# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('resources', '0012_auto_20150323_1119'),
    ]

    operations = [
        migrations.AddField(
            model_name='resourceoption',
            name='namespace',
            field=models.CharField(default=b'', max_length=155, null=True, db_index=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='resource',
            name='created_at',
            field=models.DateTimeField(default=datetime.datetime(2015, 3, 23, 12, 23, 2, 451828, tzinfo=utc), verbose_name=b'Date created', db_index=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='resource',
            name='status',
            field=models.CharField(default=b'free', max_length=25, db_index=True, choices=[(b'free', b'Free to use'), (b'inuse', b'Used by someone'), (b'failed', b'Failed resource'), (b'locked', b'Locked by business'), (b'deleted', b'Deleted')]),
            preserve_default=True,
        ),
    ]
