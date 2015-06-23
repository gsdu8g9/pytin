# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('assets', '0004_auto_20150623_1649'),
    ]

    operations = [
        migrations.DeleteModel(
            name='InventoryResource',
        ),
    ]
