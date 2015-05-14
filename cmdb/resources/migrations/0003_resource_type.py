# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('resources', '0002_auto_20150514_2039'),
    ]

    operations = [
        migrations.AddField(
            model_name='resource',
            name='type',
            field=models.CharField(default=b'Resource', max_length=155, db_index=True),
        ),
    ]
