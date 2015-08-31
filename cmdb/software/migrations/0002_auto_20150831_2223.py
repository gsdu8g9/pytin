# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations

from software.models import DirectAdminLicense


def populate_new_fields(apps, schema_editor):
    for da_license in DirectAdminLicense.active.all():
        cid_value = da_license.get_option_value('cid', default='')
        if cid_value:
            da_license.cid = cid_value

            try:
                opt = da_license.get_option('cid')
                opt.delete()
            except:
                pass
        else:
            da_license.cid = 6768

        lid_value = da_license.get_option_value('lid', default='')
        if lid_value:
            da_license.lid = lid_value

            try:
                opt = da_license.get_option('lid')
                opt.delete()
            except:
                pass


class Migration(migrations.Migration):
    dependencies = [
        ('software', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(populate_new_fields),
    ]
