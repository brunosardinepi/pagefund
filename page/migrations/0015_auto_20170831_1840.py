# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2017-08-31 23:40
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('page', '0014_page_managers'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='page',
            options={'permissions': (('manager_edit', 'Manager -- edit Page'), ('manager_delete', 'Manager -- delete Page'), ('manager_invite', 'Manager -- invite users to manage Page'))},
        ),
    ]
