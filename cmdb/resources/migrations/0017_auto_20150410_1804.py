# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('resources', '0016_auto_20150403_0127'),
    ]

    operations = [
        migrations.AlterField(
            model_name='resource',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, verbose_name=b'Date created', db_index=True),
        ),
        migrations.AlterField(
            model_name='resource',
            name='parent',
            field=models.ForeignKey(default=0, to='resources.Resource', null=True),
        ),
        migrations.AlterField(
            model_name='resource',
            name='type',
            field=models.CharField(default=b'Resource', max_length=155, db_index=True),
        ),
        migrations.AlterField(
            model_name='resourceoption',
            name='updated_at',
            field=models.DateTimeField(auto_now_add=True, verbose_name=b'Date updated', db_index=True),
        ),
    ]
