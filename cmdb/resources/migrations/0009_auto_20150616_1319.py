# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('resources', '0008_auto_20150616_1141'),
    ]

    operations = [
        migrations.AlterField(
            model_name='resourceoption',
            name='namespace',
            field=models.CharField(default='', max_length=155, db_index=True),
        ),
    ]
