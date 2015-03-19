# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Resource',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=155)),
                ('created_date', models.DateTimeField(verbose_name=b'date created')),
                ('parent_id', models.ForeignKey(to='resources.Resource')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
