# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('resources', '0014_auto_20151013_1527'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='resourceoption',
            name='namespace',
        ),
    ]
