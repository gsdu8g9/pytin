# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('resources', '0006_auto_20150604_1252'),
        ('events', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='HistoryEvent',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('type', models.CharField(db_index=True, max_length=64, choices=[(b'create', b'create'), ((b'update',), b'update'), (b'delete', b'delete')])),
                ('field_name', models.CharField(max_length=155, null=True, db_index=True)),
                ('field_value', models.CharField(max_length=255, null=True, db_index=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('resource', models.ForeignKey(to='resources.Resource')),
            ],
            options={
                'db_table': 'resource_history',
            },
        ),
        migrations.DeleteModel(
            name='Event',
        ),
    ]
