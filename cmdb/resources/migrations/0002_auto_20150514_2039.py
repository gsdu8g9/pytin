# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('resources', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='resource',
            name='type',
        ),
        migrations.AddField(
            model_name='resource',
            name='content_type',
            field=models.ForeignKey(editable=False, to='contenttypes.ContentType', null=True),
        ),
    ]
