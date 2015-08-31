# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations

from assets.models import Server


def update_server_name(apps, schema_editor):
    for server in Server.active.all():
        server.name = "i%s" % server.id
        server.save()


class Migration(migrations.Migration):
    dependencies = [
        ('assets', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(update_server_name),
    ]
