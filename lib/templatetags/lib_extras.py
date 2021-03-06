from django import template
from django.contrib.contenttypes.models import ContentType

from campaign.models import VoteParticipant
from userprofile.models import UserImage


register = template.Library()

@register.filter
def content_type_pk(obj):
    if not obj:
        return False
    return ContentType.objects.get_for_model(obj).pk

@register.filter
def content_type(obj):
    if not obj:
        return False
    return str(ContentType.objects.get_for_model(obj))

@register.filter
def img_class(img, size):
    height = img.height
    width = img.width

    if height < (width - 60):
        html = "circular-landscape"
    elif height > (width + 60):
        html = "circular-portrait"
    else:
        html = "circular-square"

    if size == "small":
        html += "-sm"

    return html

@register.filter
def img_url_class(img, size):
    img = str(img)
    if img:
        try:
            img = img.split('/media/', 1)[1]
        except:
            return ""
        try:
            img = img.split('<br />', 1)[0]
        except:
            pass
        img = VoteParticipant.objects.get(image=img).image

        height = img.height
        width = img.width

        if height < (width - 60):
            html = "circular-landscape"
        elif height > (width + 60):
            html = "circular-portrait"
        else:
            html = "circular-square"

        if size == "small":
            html += "-sm"

        return html

@register.simple_tag
def get_img_from_pk(pk, type):
    if type == "user":
        return UserImage.objects.get(pk=pk)

@register.filter
def convert_to_pct(obj):
    if not obj:
        obj = 0
    return "{}%".format(int(obj * 100))

@register.simple_tag
def create_width(this_step, total_steps):
    # steps start at 1, so bring it down to 0 for the progress bar
    this_step -= 1
    return (this_step / total_steps) * 100