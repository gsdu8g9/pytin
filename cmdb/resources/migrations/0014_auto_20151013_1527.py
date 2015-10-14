# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('resources', '0013_resourcecomment'),
    ]

    operations = [
        migrations.RenameField(
            model_name='resourcecomment',
            old_name='value',
            new_name='message',
        ),
    ]
