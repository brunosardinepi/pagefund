# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2017-11-21 17:59
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('campaign', '0016_auto_20171121_0813'),
    ]

    operations = [
        migrations.CreateModel(
            name='VoteParticipant',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('description', models.TextField(blank=True)),
            ],
        ),
        migrations.AddField(
            model_name='campaign',
            name='event_location',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='campaign',
            name='vote_winner_gets',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='voteparticipant',
            name='campaign',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='campaign.Campaign'),
        ),
    ]