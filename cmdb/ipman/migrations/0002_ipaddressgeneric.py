# -*- coding: utf-8 -*-
# Generated by Django 1.9.6 on 2016-07-24 19:51
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('resources', '0016_resourceoption_journaling'),
        ('ipman', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='IPAddressGeneric',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('beauty', models.IntegerField(verbose_name='Beauty factor of the IP')),
                ('address', models.GenericIPAddressField(db_index=True, verbose_name='IPv4 address in string format')),
                ('status', models.CharField(choices=[('free', 'Free to use'), ('inuse', 'Used by someone'), ('failed', 'Failed resource'), ('locked', 'Resource is reserved'), ('deleted', 'Resource is marked to delete')], db_index=True, default='free', max_length=25)),
                ('parent', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='ipaddress', to='resources.Resource')),
                ('pool', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='resources.Resource')),
            ],
        ),
    ]
