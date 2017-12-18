import random
import os
import string
from collections import OrderedDict

from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_delete
from django.db.models import Sum
from django.dispatch import receiver
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils import timezone

from campaign.models import Campaign
from comments.models import Comment
from donation.models import Donation


class Page(models.Model):
    address_line1 = models.CharField(max_length=255)
    address_line2 = models.CharField(max_length=255, blank=True)
    admins = models.ManyToManyField('userprofile.UserProfile', related_name='page_admins', blank=True)
    city = models.CharField(max_length=255)
    created_on = models.DateTimeField(default=timezone.now)
    deleted = models.BooleanField(default=False)
    deleted_by = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)
    deleted_on = models.DateTimeField(blank=True, null=True)
    description = models.TextField(blank=True)
    ein = models.CharField(max_length=255, blank=True, null=True)
    is_sponsored = models.BooleanField(default=False)
    managers = models.ManyToManyField('userprofile.UserProfile', related_name='page_managers', blank=True)
    name = models.CharField(max_length=255, db_index=True)
    page_slug = models.SlugField(max_length=100, unique=True)
    subscribers = models.ManyToManyField('userprofile.UserProfile', related_name='subscribers', blank=True)
    stripe_account_id = models.CharField(max_length=255, blank=True, null=True)
    stripe_bank_account_id = models.CharField(max_length=255, blank=True, null=True)
    tos_accepted = models.BooleanField(default=False)
    trending_score = models.DecimalField(default=0, max_digits=10, decimal_places=1)
    website = models.CharField(max_length=128, blank=True)
    zipcode = models.CharField(max_length=5)

    CATEGORY_CHOICES = (
        ('animal', 'Animal'),
        ('environment', 'Environment'),
        ('education', 'Education'),
        ('other', 'Other'),
        ('religious', 'Religious'),
    )
    category = models.CharField(
        max_length=255,
        choices=CATEGORY_CHOICES,
        default='other',
    )

    STATE_CHOICES = (
        ('AL', 'Alabama'),
        ('AK', 'Alaska'),
        ('AZ', 'Arizona'),
        ('AR', 'Arkansas'),
        ('CA', 'California'),
        ('CO', 'Colorado'),
        ('CT', 'Connecticut'),
        ('DE', 'Delaware'),
        ('FL', 'Florida'),
        ('GA', 'Georgia'),
        ('HI', 'Hawaii'),
        ('ID', 'Idaho'),
        ('IL', 'Illinois'),
        ('IN', 'Indiana'),
        ('IA', 'Iowa'),
        ('KS', 'Kansas'),
        ('KY', 'Kentucky'),
        ('LA', 'Louisiana'),
        ('ME', 'Maine'),
        ('MD', 'Maryland'),
        ('MA', 'Massachusetts'),
        ('MI', 'Michigan'),
        ('MN', 'Minnesota'),
        ('MS', 'Mississippi'),
        ('MO', 'Missouri'),
        ('MT', 'Montana'),
        ('NE', 'Nebraska'),
        ('NV', 'Nevada'),
        ('NH', 'New Hampshire'),
        ('NJ', 'New Jersey'),
        ('NM', 'New Mexico'),
        ('NY', 'New York'),
        ('NC', 'North Carolina'),
        ('ND', 'North Dakota'),
        ('OH', 'Ohio'),
        ('OK', 'Oklahoma'),
        ('OR', 'Oregon'),
        ('PA', 'Pennsylvania'),
        ('RI', 'Rhode Island'),
        ('SC', 'South Carolina'),
        ('SD', 'South Dakota'),
        ('TN', 'Tennessee'),
        ('TX', 'Texas'),
        ('UT', 'Utah'),
        ('VT', 'Vermont'),
        ('VA', 'Virginia'),
        ('WA', 'Washington'),
        ('WV', 'West Virginia'),
        ('WI', 'Wisconsin'),
        ('WY', 'Wyoming'),
    )
    state = models.CharField(
        max_length=100,
        choices=STATE_CHOICES,
        default='',
    )

    TYPE_CHOICES = (
        ('nonprofit', 'Nonprofit'),
        ('personal', 'Personal'),
        ('religious', 'Religious'),
        ('other', 'Other'),
    )
    type = models.CharField(
        max_length=255,
        choices=TYPE_CHOICES,
        default='',
    )

    class Meta:
        permissions = (
            ('manager_edit', 'Manager -- edit Page'),
            ('manager_delete', 'Manager -- delete Page'),
            ('manager_invite', 'Manager -- invite users to manage Page'),
            ('manager_image_edit', 'Manager -- upload and edit media on Page'),
            ('manager_view_dashboard', 'Manager -- view Page dashboard'),
        )

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('page', kwargs={
            'page_slug': self.page_slug
            })

    def top_donors(self):
        donors = Donation.objects.filter(page=self).values_list('user', flat=True).distinct()
        top_donors = {}
        for d in donors:
            if d is not None:
                user = get_object_or_404(User, pk=d)
                total_amount = Donation.objects.filter(user=user, page=self, anonymous_amount=False, anonymous_donor=False).aggregate(Sum('amount')).get('amount__sum')
                if total_amount is not None:
                    top_donors[d] = {
                        'first_name': user.first_name,
                        'last_name': user.last_name,
                        'amount': total_amount
                    }
        top_donors = OrderedDict(sorted(top_donors.items(), key=lambda t: t[1]['amount'], reverse=True))
        top_donors = list(top_donors.items())[:10]
        return top_donors

    def managers_list(self):
        return self.managers.all()

    def images(self):
        return PageImage.objects.filter(page=self)

    def profile_picture(self):
        try:
            return PageImage.objects.get(page=self, profile_picture=True)
        except PageImage.MultipleObjectsReturned:
            # create an exception for future use
            print("multiple profile images returned")

    def active_campaigns(self):
        return Campaign.objects.filter(page=self, is_active=True, deleted=False).order_by('name')

    def inactive_campaigns(self):
        return Campaign.objects.filter(page=self, is_active=False, deleted=False)

    def comments(self):
        return Comment.objects.filter(page=self, deleted=False).order_by('-date')

    def donations(self):
        return Donation.objects.filter(page=self).order_by('-date')

    def donation_count(self):
        return Donation.objects.filter(page=self).count()

    def donation_money(self):
        return Donation.objects.filter(page=self).aggregate(Sum('amount')).get('amount__sum')

    def unique_donors(self):
        return Donation.objects.filter(page=self).distinct('donor_first_name').distinct('donor_last_name').count()

def create_random_string(length=30):
    if length <= 0:
        length = 30

    symbols = string.ascii_lowercase + string.ascii_uppercase + string.digits
    return ''.join([random.choice(symbols) for x in range(length)])

def upload_to(instance, filename):
    ext = filename.split('.')[-1]
    filename = "media/pages/images/%s.%s" % (create_random_string(), ext)
    return filename

class PageImage(models.Model):
    page = models.ForeignKey('page.Page', on_delete=models.CASCADE)
    image = models.FileField(upload_to=upload_to, blank=True, null=True)
    caption = models.CharField(max_length=255, blank=True)
    profile_picture = models.BooleanField(default=False)
    uploaded_at = models.DateTimeField(default=timezone.now)
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE)

@receiver(post_delete, sender=PageImage)
def auto_delete_file_on_delete(sender, instance, **kwargs):
    if instance.image:
        if os.path.isfile(instance.image.path):
            os.remove(instance.image.path)
