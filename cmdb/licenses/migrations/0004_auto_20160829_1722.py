# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2016-08-29 14:22
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('resources', '0019_auto_20160827_2204'),
        ('ipman', '0012_auto_20160816_2325'),
        ('licenses', '0003_directadminlicense_pool'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='directadminlicense',
            name='pool',
        ),
        migrations.RemoveField(
            model_name='directadminlicense',
            name='resource_ptr',
        ),
        migrations.DeleteModel(
            name='DirectAdminLicense',
        ),
    ]
