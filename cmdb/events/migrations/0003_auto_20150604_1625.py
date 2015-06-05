# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0002_auto_20150604_1557'),
    ]

    operations = [
        migrations.RenameField(
            model_name='historyevent',
            old_name='field_value',
            new_name='field_new_value',
        ),
        migrations.AddField(
            model_name='historyevent',
            name='field_old_value',
            field=models.CharField(max_length=255, null=True, db_index=True),
        ),
    ]
