# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0003_auto_20150604_1625'),
    ]

    operations = [
        migrations.AlterField(
            model_name='historyevent',
            name='created_at',
            field=models.DateTimeField(db_index=True),
        ),
        migrations.AlterField(
            model_name='historyevent',
            name='type',
            field=models.CharField(db_index=True, max_length=64, choices=[(b'create', b'create'), (b'update', b'update'), (b'delete', b'delete')]),
        ),
    ]
