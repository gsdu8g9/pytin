# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('resources', '0009_auto_20150616_1319'),
    ]

    operations = [
        migrations.AlterField(
            model_name='resourceoption',
            name='format',
            field=models.CharField(default='string', max_length=25, db_index=True, choices=[('dict', 'Dictionary string'), ('int', 'Integer value'), ('bool', 'Boolean value'), ('float', 'Float value'), ('string', 'String value')]),
        ),
    ]
