from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class StripePlan(models.Model):
    amount = models.IntegerField()
    date = models.DateTimeField(default=timezone.now)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    campaign = models.ForeignKey('campaign.Campaign', on_delete=models.CASCADE, blank=True, null=True)
    page = models.ForeignKey('page.Page', on_delete=models.CASCADE, blank=True, null=True)
    stripe_plan_id = models.CharField(max_length=255, blank=True)
    stripe_subscription_id = models.CharField(max_length=255, blank=True)
    INTERVAL_CHOICES = (
        ('month', 'Monthly'),
    )
    interval = models.CharField(
        max_length=20,
        choices=INTERVAL_CHOICES,
        default='month',
    )

    def __str__(self):
        return "%s%s-%s" % (self.user.first_name, self.user.last_name, self.pk)
