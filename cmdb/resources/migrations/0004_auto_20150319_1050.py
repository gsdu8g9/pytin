# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('resources', '0003_auto_20150319_1046'),
    ]

    operations = [
        migrations.AlterField(
            model_name='resource',
            name='created_date',
            field=models.DateTimeField(auto_now=True, verbose_name=b'date created'),
            preserve_default=True,
        ),
    ]
