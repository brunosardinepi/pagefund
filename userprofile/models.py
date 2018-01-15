from collections import OrderedDict
from itertools import chain
import os
import random
import string

from django.db import models
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from django.urls import reverse
from django.utils import timezone

from allauth.account.signals import user_signed_up
import stripe

from donation.models import Donation
from invitations.models import ManagerInvitation
from pagefund import config, settings
from pagefund.utils import email
from plans.models import StripePlan


stripe.api_key = config.settings['stripe_api_sk']

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    birthday = models.DateField(blank=True, null=True)
    stripe_customer_id = models.CharField(max_length=255, blank=True, null=True)
    notification_email_pagefund_news = models.BooleanField(default=True)
    notification_email_page_created = models.BooleanField(default=True)
    notification_email_campaign_created = models.BooleanField(default=True)
    notification_email_page_manager = models.BooleanField(default=True)
    notification_email_campaign_manager = models.BooleanField(default=True)
    notification_email_page_donation = models.BooleanField(default=True)
    notification_email_recurring_donation = models.BooleanField(default=True)
    notification_email_campaign_donation = models.BooleanField(default=True)
    notification_email_campaign_voted = models.BooleanField(default=True)
    notification_email_campaign_ticket_purchased = models.BooleanField(default=True)
    notification_email_campaign_goal_reached = models.BooleanField(default=True)
    notification_email_campaign_ticket_sold_out = models.BooleanField(default=True)
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

    def __str__(self):
        return ("%s %s" % (self.user.first_name, self.user.last_name))

    def get_absolute_url(self):
        return reverse('userprofile:userprofile')

    def is_admin(self, obj):
        name = type(obj).__name__
        if name == "Campaign":
            return self in obj.campaign_admins.all()
        elif name == "Page":
            return self in obj.admins.all()

    def is_manager(self, obj):
        name = type(obj).__name__
        if name == "Campaign":
            return self in obj.campaign_managers.all()
        elif name == "Page":
            return self in obj.managers.all()

    def donations(self):
        return Donation.objects.filter(user=self.user).order_by('-date')

    def images(self):
        return UserImage.objects.filter(user=self)

    def invitations(self):
        return ManagerInvitation.objects.filter(invite_from=self.user, expired=False)

    def my_campaigns(self):
        admin_campaigns = self.campaign_admins.filter(deleted=False)
        manager_campaigns = self.campaign_managers.filter(deleted=False)
        subscribed_campaigns = self.campaign_subscribers.filter(deleted=False)
        campaigns = list(chain(admin_campaigns, manager_campaigns, subscribed_campaigns))
        campaigns = sorted(set(campaigns),key=lambda x: x.name)
        return campaigns

    def my_pages(self):
        admin_pages = self.page_admins.filter(deleted=False)
        manager_pages = self.page_managers.filter(deleted=False)
        subscribed_pages = self.subscribers.filter(deleted=False)
        pages = list(chain(admin_pages, manager_pages, subscribed_pages))
        pages = sorted(set(pages),key=lambda x: x.name)
        return pages

    def notification_preferences(self):
        notifications = OrderedDict()
        notifications["notification_email_pagefund_news"] = {
            "value": self.notification_email_pagefund_news,
            "label": "PageFund news"
        }
        notifications["notification_email_page_created"] = {
            "value": self.notification_email_page_created,
            "label": "Page created"
        }
        notifications["notification_email_campaign_created"] = {
            "value": self.notification_email_campaign_created,
            "label": "Campaign created"
        }
        notifications["notification_email_page_manager"] = {
            "value": self.notification_email_page_manager,
            "label": "Page manager invitation"
        }
        notifications["notification_email_campaign_manager"] = {
            "value": self.notification_email_campaign_manager,
            "label": "Campaign manager invitation"
        }
        notifications["notification_email_page_donation"] = {
            "value": self.notification_email_page_donation,
            "label": "Page donation"
        }
        notifications["notification_email_recurring_donation"] = {
            "value": self.notification_email_recurring_donation,
            "label": "Recurring donation setup"
        }
        notifications["notification_email_campaign_donation"] = {
            "value": self.notification_email_campaign_donation,
            "label": "Campaign donation"
        }
        notifications["notification_email_campaign_voted"] = {
            "value": self.notification_email_campaign_voted,
            "label": "Voted in Campaign"
        }
        notifications["notification_email_campaign_ticket_purchased"] = {
            "value": self.notification_email_campaign_ticket_purchased,
            "label": "Ticket purchased"
        }
        notifications["notification_email_campaign_goal_reached"] = {
            "value": self.notification_email_campaign_goal_reached,
            "label": "Campaign goal reached"
        }
        notifications["notification_email_campaign_ticket_sold_out"] = {
            "value": self.notification_email_campaign_ticket_sold_out,
            "label": "Campaign tickets sold out"
        }
        return notifications

    def plans(self):
        return StripePlan.objects.filter(user=self.user)

    def profile_picture(self):
        try:
            return UserImage.objects.get(user=self, profile_picture=True)
        except UserImage.DoesNotExist:
            return None

    def saved_cards(self):
        return StripeCard.objects.filter(user=self.user.userprofile)

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.userprofile.save()

@receiver(user_signed_up, dispatch_uid="user_signed_up")
def user_signed_up_(request, user, **kwargs):
    if not settings.TESTING:
        metadata = {'user_pk': user.pk}
        customer = stripe.Customer.create(
            email=user.email,
            metadata=metadata
        )

        user.userprofile.stripe_customer_id = customer.id
        user.save()

    email(user.email, "blank", "blank", "new_user_sign_up")

def create_random_string(length=30):
    if length <= 0:
        length = 30

    symbols = string.ascii_lowercase + string.ascii_uppercase + string.digits
    return ''.join([random.choice(symbols) for x in range(length)])

def upload_to(instance, filename):
    ext = filename.split('.')[-1]
    filename = "media/user/images/%s.%s" % (create_random_string(), ext)
    return filename

class UserImage(models.Model):
    user = models.ForeignKey('userprofile.UserProfile', on_delete=models.CASCADE)
    image = models.FileField(upload_to=upload_to, max_length=255, blank=True, null=True)
    caption = models.CharField(max_length=255, blank=True)
    profile_picture = models.BooleanField(default=False)

@receiver(post_delete, sender=UserImage)
def auto_delete_file_on_delete(sender, instance, **kwargs):
    if instance.image:
        if os.path.isfile(instance.image.path):
            os.remove(instance.image.path)

class StripeCard(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    stripe_card_id = models.CharField(max_length=255)
    stripe_card_fingerprint = models.CharField(max_length=255)
    name = models.CharField(max_length=255, blank=True)
    default = models.BooleanField(default=False)
    uploaded_at = models.DateTimeField(default=timezone.now)
