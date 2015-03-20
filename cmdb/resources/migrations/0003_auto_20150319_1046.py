# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('resources', '0002_auto_20150319_1036'),
    ]

    operations = [
        migrations.AlterField(
            model_name='resource',
            name='parent_id',
            field=models.ForeignKey(default=0, to='resources.Resource'),
            preserve_default=True,
        ),
    ]
