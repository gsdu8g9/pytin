# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2016-08-28 17:43
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('licenses', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='directadminlicense',
            name='ip_address',
        ),
    ]
