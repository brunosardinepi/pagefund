# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2017-08-22 20:53
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('page', '0012_auto_20170822_2045'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='page',
            options={'permissions': (('manager_edit_page', 'Manager -- edit Page'), ('manager_delete_page', 'Manager -- delete Page'), ('manager_invite_page', 'Manager -- invite users to manage Page'))},
        ),
    ]