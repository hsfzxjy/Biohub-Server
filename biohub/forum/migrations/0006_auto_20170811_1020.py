# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2017-08-11 09:20
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('forum', '0005_auto_20170810_1444'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='brick',
            name='star_users',
        ),
        migrations.RemoveField(
            model_name='experience',
            name='rate_num',
        ),
        migrations.RemoveField(
            model_name='experience',
            name='rate_score',
        ),
        migrations.RemoveField(
            model_name='experience',
            name='rate_users',
        ),
        migrations.AddField(
            model_name='brick',
            name='rate_num',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='brick',
            name='rate_score',
            field=models.DecimalField(decimal_places=1, default=0, max_digits=2),
        ),
        migrations.AddField(
            model_name='brick',
            name='rate_users',
            field=models.ManyToManyField(related_name='bricks_rated', to=settings.AUTH_USER_MODEL),
        ),
    ]
