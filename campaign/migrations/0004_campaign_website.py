# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2018-01-16 03:25
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('campaign', '0003_auto_20180115_2117'),
    ]

    operations = [
        migrations.AddField(
            model_name='campaign',
            name='website',
            field=models.CharField(blank=True, max_length=128),
        ),
    ]