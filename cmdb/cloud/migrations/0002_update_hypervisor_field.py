# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations

from resources.models import ResourceOption


def update_field_name(apps, schema_editor):
    ResourceOption.objects.filter(name='hypervisor_tech').update(name='hypervisor_driver')


class Migration(migrations.Migration):
    dependencies = [
        ('cloud', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(update_field_name),
    ]
