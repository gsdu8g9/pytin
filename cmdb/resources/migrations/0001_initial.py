# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Resource',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(default=b'Resource', max_length=155, db_index=True)),
                ('type', models.CharField(default=b'Resource', max_length=155, db_index=True)),
                ('status', models.CharField(default=b'free', max_length=25, db_index=True, choices=[(b'free', b'Free to use'), (b'inuse', b'Used by someone'), (b'failed', b'Failed resource'), (b'locked', b'Locked by business'), (b'deleted', b'Deleted')])),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name=b'Date created', db_index=True)),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name=b'Date updated', db_index=True)),
                ('parent', models.ForeignKey(default=None, to='resources.Resource', null=True)),
            ],
            options={
                'db_table': 'resources',
            },
        ),
        migrations.CreateModel(
            name='ResourceOption',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=155, db_index=True)),
                ('namespace', models.CharField(default=b'', max_length=155, db_index=True)),
                ('updated_at', models.DateTimeField(auto_now_add=True, verbose_name=b'Date updated', db_index=True)),
                ('format', models.CharField(default=b'string', max_length=25, db_index=True, choices=[(b'dict', b'Dictionary string'), (b'int', b'Integer value'), (b'float', b'Float value'), (b'string', b'String value')])),
                ('value', models.TextField(verbose_name=b'Option value')),
                ('resource', models.ForeignKey(to='resources.Resource')),
            ],
            options={
                'db_table': 'resource_options',
            },
        ),
    ]
