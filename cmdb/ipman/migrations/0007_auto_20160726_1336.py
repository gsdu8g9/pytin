# -*- coding: utf-8 -*-
# Generated by Django 1.9.6 on 2016-07-26 10:36
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ipman', '0006_auto_20160726_1333'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ipaddressgeneric',
            name='address',
            field=models.GenericIPAddressField(db_index=True, unique=True, verbose_name='IPv4 address in string format'),
        ),
    ]
