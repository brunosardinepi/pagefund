# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2018-01-28 16:19
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import page.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('userprofile', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Page',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('address_line1', models.CharField(max_length=255)),
                ('address_line2', models.CharField(blank=True, max_length=255)),
                ('city', models.CharField(max_length=255)),
                ('created_on', models.DateTimeField(default=django.utils.timezone.now)),
                ('deleted', models.BooleanField(default=False)),
                ('deleted_on', models.DateTimeField(blank=True, null=True)),
                ('description', models.TextField(blank=True)),
                ('ein', models.CharField(blank=True, max_length=255)),
                ('is_sponsored', models.BooleanField(default=False)),
                ('name', models.CharField(db_index=True, max_length=255)),
                ('page_slug', models.SlugField(max_length=255, unique=True)),
                ('stripe_account_id', models.CharField(blank=True, max_length=255)),
                ('stripe_bank_account_id', models.CharField(blank=True, max_length=255)),
                ('tos_accepted', models.BooleanField(default=False)),
                ('trending_score', models.DecimalField(decimal_places=1, default=0, max_digits=10)),
                ('website', models.CharField(blank=True, max_length=128)),
                ('zipcode', models.CharField(max_length=5)),
                ('category', models.CharField(choices=[('animal', 'Animal'), ('arts', 'Arts'), ('community', 'Community'), ('education', 'Education'), ('emergencies', 'Emergencies'), ('environmental', 'Environmental'), ('family', 'Family'), ('humanitarian', 'Humanitarian Aid'), ('medical', 'Medical'), ('memorial', 'Memorial'), ('other', 'Other'), ('religious', 'Religious'), ('sports', 'Sports'), ('stem', 'STEM (Science, Technology, Engineering, and Math)'), ('veterans', 'Veterans')], default='other', max_length=255)),
                ('state', models.CharField(choices=[('AL', 'Alabama'), ('AK', 'Alaska'), ('AZ', 'Arizona'), ('AR', 'Arkansas'), ('CA', 'California'), ('CO', 'Colorado'), ('CT', 'Connecticut'), ('DE', 'Delaware'), ('FL', 'Florida'), ('GA', 'Georgia'), ('HI', 'Hawaii'), ('ID', 'Idaho'), ('IL', 'Illinois'), ('IN', 'Indiana'), ('IA', 'Iowa'), ('KS', 'Kansas'), ('KY', 'Kentucky'), ('LA', 'Louisiana'), ('ME', 'Maine'), ('MD', 'Maryland'), ('MA', 'Massachusetts'), ('MI', 'Michigan'), ('MN', 'Minnesota'), ('MS', 'Mississippi'), ('MO', 'Missouri'), ('MT', 'Montana'), ('NE', 'Nebraska'), ('NV', 'Nevada'), ('NH', 'New Hampshire'), ('NJ', 'New Jersey'), ('NM', 'New Mexico'), ('NY', 'New York'), ('NC', 'North Carolina'), ('ND', 'North Dakota'), ('OH', 'Ohio'), ('OK', 'Oklahoma'), ('OR', 'Oregon'), ('PA', 'Pennsylvania'), ('RI', 'Rhode Island'), ('SC', 'South Carolina'), ('SD', 'South Dakota'), ('TN', 'Tennessee'), ('TX', 'Texas'), ('UT', 'Utah'), ('VT', 'Vermont'), ('VA', 'Virginia'), ('WA', 'Washington'), ('WV', 'West Virginia'), ('WI', 'Wisconsin'), ('WY', 'Wyoming')], default='', max_length=100)),
                ('type', models.CharField(choices=[('nonprofit', 'Nonprofit'), ('personal', 'Personal'), ('other', 'Other')], default='', max_length=255)),
                ('admins', models.ManyToManyField(blank=True, related_name='page_admins', to='userprofile.UserProfile')),
                ('deleted_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('managers', models.ManyToManyField(blank=True, related_name='page_managers', to='userprofile.UserProfile')),
                ('subscribers', models.ManyToManyField(blank=True, related_name='subscribers', to='userprofile.UserProfile')),
            ],
            options={
                'permissions': (('manager_edit', 'Manager -- edit Page'), ('manager_delete', 'Manager -- delete Page'), ('manager_invite', 'Manager -- invite users to manage Page'), ('manager_image_edit', 'Manager -- upload and edit media on Page'), ('manager_view_dashboard', 'Manager -- view Page dashboard')),
            },
        ),
        migrations.CreateModel(
            name='PageImage',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', models.FileField(blank=True, upload_to=page.models.upload_to)),
                ('caption', models.CharField(blank=True, max_length=255)),
                ('profile_picture', models.BooleanField(default=False)),
                ('uploaded_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('width', models.IntegerField(null=True)),
                ('height', models.IntegerField(null=True)),
                ('page', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='page.Page')),
                ('uploaded_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
