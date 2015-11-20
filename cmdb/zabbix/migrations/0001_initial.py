# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('resources', '0015_remove_resourceoption_namespace'),
    ]

    operations = [
        migrations.CreateModel(
            name='ZabbixMetric',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('zbx_metric_id', models.IntegerField(verbose_name=b'Metric ID from Zabbix.', db_index=True)),
                ('cmdb_node_option', models.ForeignKey(to='resources.ResourceOption')),
            ],
        ),
    ]
