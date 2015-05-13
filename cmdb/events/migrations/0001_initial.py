# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Event',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('source_object_id', models.PositiveIntegerField(null=True, db_index=True)),
                ('source_model', models.CharField(max_length=64, null=True, db_index=True)),
                ('type', models.CharField(max_length=64, db_index=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('data', models.TextField(null=True)),
            ],
            options={
                'db_table': 'events',
            },
        ),
    ]
