# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.utils import timezone


class Migration(migrations.Migration):

    dependencies = [
        ('resources', '0005_auto_20150522_1159'),
    ]

    operations = [
        migrations.AlterField(
            model_name='resource',
            name='last_seen',
            field=models.DateTimeField(default=timezone.now, verbose_name=b'Date last seen', db_index=True),
        ),
    ]
