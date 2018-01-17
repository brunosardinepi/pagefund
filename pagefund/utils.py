import urllib.request as urllib

from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.shortcuts import get_object_or_404, redirect

from guardian.shortcuts import assign_perm, get_user_perms, remove_perm
import sendgrid
from sendgrid.helpers.mail import *

from . import config, settings


def email(user_email, subject, body, template):
    if not settings.TESTING:
        templates = {
            "page_manager_invitation": "d6a60dee-9e61-41e5-954e-0e049e95d0ed",
            "new_campaign_created": "d5952e1d-3672-4876-97a1-7b5ee3c2fef7",
            "new_page_created": "0ba093a3-5628-4da9-b3e5-267f9f0313c4",
            "new_user_signup": "0f0ff154-4a0e-48eb-b073-d59447ac67e8",
            "page_bank_information_updated": "c988f1b2-ded9-476b-85a1-a7b1ec3a55e7",
            "pagefund_invitation": "09db718c-d1bb-446c-9cf5-67cd0adf0c97",
            "forgot_password": "3fcbedb0-d54b-49b3-885e-856bbbaf21c8",
            "note": "",
        }
        sg = sendgrid.SendGridAPIClient(apikey=config.settings["sendgrid_api_key"])
        from_email = Email("no-reply@page.fund")
        to_email = Email(user_email)
        subject = subject
        content = Content("text/plain", body)
        mail = Mail(from_email, subject, to_email, content)
        if template:
            mail.template_id = templates[template]
        try:
            response = sg.client.mail.send.post(request_body=mail.get())
        except urllib.HTTPError as e:
            print(e.read())
            exit()

def update_manager_permissions(post_data, type):
#    post_data = request.POST.getlist('permissions[]')
    new_permissions = dict()
    for p in post_data:
        m = p.split("_", 1)[0]
        p = p.split("_", 1)[1]
        if m not in new_permissions:
            new_permissions[m] = []
        new_permissions[m].append(p)

    # get list of user's current perms
    old_permissions = dict()
    for k in new_permissions:
        user = get_object_or_404(User, pk=k)
        user_permissions = get_user_perms(user, type)
        if k not in old_permissions:
            old_permissions[k] = []
        for p in user_permissions:
            old_permissions[k].append(p)

    # for every item in the user's current perms, compare to the new list of perms from the form
    for k, v in old_permissions.items():
        user = get_object_or_404(User, pk=k)
        for e in v:
            # if that item is in the list, remove it from the new list and do nothing to the perm
            if e in new_permissions[k]:
                new_permissions[k].remove(e)
            # if that item is not in the list, remove the perm
            else:
                remove_perm(e, user, type)
    # for every item in the new list, give the user the perms for that item
    for k,v in new_permissions.items():
        user = get_object_or_404(User, pk=k)
        for e in v:
            assign_perm(e, user, type)

def donation_amount(initial_amount):
    stripe_fee = int(initial_amount * 0.029) + 30
    pagefund_fee = int(initial_amount * config.settings['pagefund_fee'])
    return initial_amount - stripe_fee - pagefund_fee

def has_dashboard_access(user, obj, permission):
    # user needs to be an admin,
    # or if there's a permission, then they need to be a manager with that permission.
    # otherwise, just a manager

    if user.userprofile.is_admin(obj):
        return True
    elif user.userprofile.is_manager(obj):
        if permission:
            if user.has_perm(permission, obj):
                return True
            else:
                return False
        else:
            return True
    else:
        return False

def get_content_type(pk):
    return ContentType.objects.get(pk=pk)
