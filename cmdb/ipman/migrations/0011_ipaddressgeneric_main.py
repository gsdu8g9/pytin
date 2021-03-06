# -*- coding: utf-8 -*-
# Generated by Django 1.9.6 on 2016-08-16 08:04
from __future__ import unicode_literals

from django.db import migrations, models

from ipman.models import IPAddressGeneric


def migrate_ips(apps, schema_editor):
    IPAddress = apps.get_model("ipman", "IPAddress")

    if not IPAddress.objects.filter().exists():
        return

    for new_ip in IPAddressGeneric.objects.all():
        old_ips = IPAddress.objects.filter(address=new_ip.address)
        if len(old_ips) > 0:
            new_ip.main = old_ips[0].get_option_value('main', default=False)
            new_ip.save()


class Migration(migrations.Migration):
    dependencies = [
        ('ipman', '0010_auto_20160813_1406'),
    ]

    operations = [
        migrations.AddField(
            model_name='ipaddressgeneric',
            name='main',
            field=models.BooleanField(db_index=True, default=False, verbose_name='Main IP of the device'),
        ),
        migrations.RunPython(migrate_ips),
    ]
