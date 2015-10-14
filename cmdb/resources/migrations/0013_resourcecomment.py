# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('resources', '0012_auto_20151011_0048'),
    ]

    operations = [
        migrations.CreateModel(
            name='ResourceComment',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Date created', db_index=True)),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Date updated', db_index=True)),
                ('value', models.TextField(verbose_name='Comment text')),
                ('author', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
                ('resource', models.ForeignKey(to='resources.Resource')),
            ],
        ),
    ]
