# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('resources', '0007_auto_20150608_1523'),
    ]

    operations = [
        migrations.AlterField(
            model_name='resourceoption',
            name='namespace',
            field=models.CharField(default='', max_length=155, null=True, db_index=True),
        ),
    ]
