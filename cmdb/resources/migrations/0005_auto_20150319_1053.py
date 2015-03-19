# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('resources', '0004_auto_20150319_1050'),
    ]

    operations = [
        migrations.RenameField(
            model_name='resource',
            old_name='parent_id',
            new_name='parent',
        ),
        migrations.AlterField(
            model_name='resource',
            name='created_date',
            field=models.DateTimeField(verbose_name=b'date created', auto_created=True),
            preserve_default=True,
        ),
    ]
