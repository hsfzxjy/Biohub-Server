# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2017-08-06 07:46
from __future__ import unicode_literals

import biohub.accounts.models
import biohub.accounts.validators
from django.conf import settings
import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('username', models.CharField(error_messages={'unique': 'A user with that username already exists.'}, max_length=20, unique=True, validators=[biohub.accounts.validators.UsernameValidator()], verbose_name='username')),
                ('email', models.EmailField(blank=True, max_length=254, verbose_name='email address')),
                ('avatar_url', models.URLField(blank=True, verbose_name='avatar url')),
                ('address', models.CharField(blank=True, max_length=200, validators=[django.core.validators.MaxLengthValidator(200)], verbose_name='address')),
                ('site_url', models.URLField(blank=True, verbose_name='personal site url')),
                ('description', models.TextField(blank=True, verbose_name='personal description')),
                ('followers', models.ManyToManyField(related_name='following', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
            managers=[
                ('objects', biohub.accounts.models.UserManager()),
            ],
        ),
    ]
