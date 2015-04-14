# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('resources', '0017_auto_20150410_1804'),
    ]

    operations = [
        migrations.AlterField(
            model_name='resource',
            name='parent',
            field=models.ForeignKey(default=None, to='resources.Resource', null=True),
        ),
    ]
