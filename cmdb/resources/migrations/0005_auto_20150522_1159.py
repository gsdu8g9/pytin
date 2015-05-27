# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('resources', '0004_resource_last_seen'),
    ]

    operations = [
        migrations.AlterField(
            model_name='resource',
            name='last_seen',
            field=models.DateTimeField(default=django.utils.timezone.now, verbose_name=b'Date last seen', db_index=True),
        ),
    ]
