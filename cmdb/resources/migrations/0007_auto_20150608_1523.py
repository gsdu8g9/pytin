# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('resources', '0006_auto_20150604_1252'),
    ]

    operations = [
        migrations.AlterField(
            model_name='resource',
            name='status',
            field=models.CharField(default=b'free', max_length=25, db_index=True, choices=[(b'free', b'Free to use'), (b'inuse', b'Used by someone'), (b'failed', b'Failed resource'), (b'locked', b'Resource is reserved'), (b'deleted', b'Resource is marked to delete')]),
        ),
    ]
