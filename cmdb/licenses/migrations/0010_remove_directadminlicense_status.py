# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2016-08-29 15:57
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('licenses', '0009_auto_20160829_1807'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='directadminlicense',
            name='status',
        ),
    ]
