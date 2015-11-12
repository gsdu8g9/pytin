# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='CloudTaskTracker',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('task_class', models.CharField(max_length=55, verbose_name='Python class of the cloud task.', db_index=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Date created', db_index=True)),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Date updated', db_index=True)),
                ('status', models.CharField(default='new', max_length=25, db_index=True, choices=[('new', 'Request created.'), ('progress', 'Request in progress.'), ('success', 'Request completed.'), ('failed', 'Request failed.')])),
                ('context_json', models.TextField(verbose_name='Cloud command context.')),
                ('return_json', models.TextField(verbose_name='Cloud command return data.')),
                ('error', models.TextField(verbose_name='Error message in case of failed state.')),
            ],
        ),
    ]
