# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('resources', '0015_remove_resourceoption_namespace'),
    ]

    operations = [
        migrations.CreateModel(
            name='CloudNode',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('heartbeat_last', models.DateTimeField(null=True, verbose_name=b'Last received heartbeat', db_index=True)),
                ('fail_count', models.IntegerField(default=0, verbose_name=b'Number of registered errors')),
                ('resource', models.OneToOneField(default=None, to='resources.Resource')),
            ],
        ),
        migrations.CreateModel(
            name='CloudService',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(default=None, max_length=25, verbose_name=b'Service name.', db_index=True)),
                ('implementor', models.CharField(default=None, max_length=155, verbose_name=b'Implementation class name.')),
            ],
        ),
        migrations.AddField(
            model_name='cloudnode',
            name='service',
            field=models.ForeignKey(default=0, to='cloud.CloudService'),
        ),
    ]
