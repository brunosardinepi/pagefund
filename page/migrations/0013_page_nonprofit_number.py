# -*- coding: utf-8 -*-
# Generated by Django 1.11.5 on 2017-09-28 16:05
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('page', '0012_auto_20170927_2204'),
    ]

    operations = [
        migrations.AddField(
            model_name='page',
            name='nonprofit_number',
            field=models.CharField(blank=True, max_length=255),
        ),
    ]
