from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class CommentTemplate(models.Model):
    content = models.TextField(blank=True)
    date = models.DateTimeField(default=timezone.now)
    deleted = models.BooleanField(default=False)
    deleted_on = models.DateTimeField(blank=True, null=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        abstract = True


class Comment(CommentTemplate):
    campaign = models.ForeignKey('campaign.Campaign', on_delete=models.CASCADE, blank=True, null=True)
    page = models.ForeignKey('page.Page', on_delete=models.CASCADE, blank=True, null=True)

    def __str__(self):
        if self.page:
            return "Page;%s;%s;%s" % (self.page.name, self.user, self.date)
        elif self.campaign:
            return "Campaign;%s;%s;%s" % (self.campaign.name, self.user, self.date)

    def get_absolute_url(self):
        if self.page:
            return reverse('page', kwargs={'page_slug': self.page.page_slug})
        elif self.campaign:
            return reverse('campaign', kwargs={
                'page_slug': self.campaign.page.page_slug,
                'campaign_pk': self.campaign.pk,
                'campaign_slug': self.campaign.campaign_slug
            })

    def get_fields(self):
        return [(field.name, field.value_to_string(self)) for field in Comment._meta.fields]


class Reply(CommentTemplate):
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE)

    class Meta:
        verbose_name_plural = "replies"
