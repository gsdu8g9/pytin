# -*- coding: utf-8 -*-
# Generated by Django 1.9.6 on 2016-07-26 10:33
from __future__ import unicode_literals

import datetime
from django.db import migrations, models
from django.utils.timezone import utc
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('ipman', '0005_auto_20160725_1758'),
    ]

    operations = [
        migrations.AddField(
            model_name='ipaddressgeneric',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, db_index=True, default=datetime.datetime(2016, 7, 26, 10, 33, 30, 790213, tzinfo=utc), verbose_name='Date created'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='ipaddressgeneric',
            name='last_seen',
            field=models.DateTimeField(db_index=True, default=django.utils.timezone.now, verbose_name='Date last seen'),
        ),
        migrations.AddField(
            model_name='ipaddressgeneric',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, db_index=True, default=django.utils.timezone.now, verbose_name='Date updated'),
            preserve_default=False,
        ),
    ]
