# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2016-08-29 15:21
from __future__ import unicode_literals

from django.db import migrations

from resources.models import Resource


def remove_licenses(apps, schema_editor):
    Resource.objects.filter(type='licenses.directadmin').delete()


class Migration(migrations.Migration):
    dependencies = [
        ('resources', '0019_auto_20160827_2204'),
    ]

    operations = [
        migrations.RunPython(remove_licenses),
    ]
