# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='CloudService',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=25, verbose_name='Service name.', db_index=True)),
                ('implementor', models.CharField(default=None, max_length=155, verbose_name='Implementation class name.')),
                ('active', models.BooleanField(default=False, db_index=True, verbose_name='Set if service is active.')),
            ],
        ),
        migrations.CreateModel(
            name='ServiceRequestTracker',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('target', models.CharField(max_length=55, verbose_name='Target cloud service name.', db_index=True)),
                ('type', models.CharField(max_length=55, verbose_name='Request type.', db_index=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Date created', db_index=True)),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Date updated', db_index=True)),
                ('status', models.CharField(default='progress', max_length=25, db_index=True, choices=[('progress', 'Request in progress.'), ('success', 'Request completed.'), ('failed', 'Request failed.')])),
                ('json_options', models.TextField(verbose_name='Comment text')),
                ('json_response', models.TextField(verbose_name='Comment text')),
            ],
        ),
    ]
