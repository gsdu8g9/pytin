# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('resources', '0007_auto_20150319_1103'),
    ]

    operations = [
        migrations.CreateModel(
            name='ResourceHistory',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=155, db_index=True)),
                ('value', models.TextField(verbose_name=b'Option value')),
                ('updated_at', models.DateTimeField(auto_now_add=True, verbose_name=b'History date', db_index=True)),
                ('resource', models.ForeignKey(to='resources.Resource')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ResourceOption',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=155, db_index=True)),
                ('value', models.TextField(verbose_name=b'Option value')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name=b'Date updated', db_index=True)),
                ('resource', models.ForeignKey(to='resources.Resource')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AlterField(
            model_name='resource',
            name='created_at',
            field=models.DateTimeField(default=datetime.datetime(2015, 3, 19, 15, 49, 55, 741428, tzinfo=utc), verbose_name=b'Date created', db_index=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='resource',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, verbose_name=b'Date updated', db_index=True),
            preserve_default=True,
        ),
    ]
