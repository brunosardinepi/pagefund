# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2017-08-31 19:35
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('page', '0011_page_is_sponsored'),
    ]

    operations = [
        migrations.AddField(
            model_name='page',
            name='icon',
            field=models.ImageField(blank=True, null=True, upload_to='media/pages/'),
        ),
    ]