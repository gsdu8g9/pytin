# -*- coding: utf-8 -*-
# Generated by Django 1.9.6 on 2016-07-26 22:11
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0009_auto_20160727_0055'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='historyevent',
            name='resource',
        ),
    ]
