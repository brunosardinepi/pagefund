# -*- coding: utf-8 -*-
# Generated by Django 1.11.5 on 2017-09-18 18:21
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('page', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='pageicon',
            name='page',
        ),
        migrations.DeleteModel(
            name='PageIcon',
        ),
    ]
