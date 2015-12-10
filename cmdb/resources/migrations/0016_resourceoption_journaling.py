# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('resources', '0015_remove_resourceoption_namespace'),
    ]

    operations = [
        migrations.AddField(
            model_name='resourceoption',
            name='journaling',
            field=models.BooleanField(default=True),
        ),
    ]
