import json

from django.contrib.auth.models import User
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

import stripe

from campaign.models import Campaign
from donation.models import Donation
from page.models import Page
from plans.models import StripePlan


@require_POST
@csrf_exempt
def charge_succeeded(request):
    event_json = json.loads(request.body.decode('utf-8'))
    print(json.dumps(event_json, indent=4, sort_keys=True))

    if not event_json['data']['object']['metadata']:
        print("metadata is empty")
        invoice = stripe.Invoice.retrieve(event_json['data']['object']['invoice'])
        print("invoice")
        print(invoice)
        subscription = stripe.Subscription.retrieve(invoice['subscription'])
        print("subscription")
        print(subscription)
        anonymous_amount = subscription['plan']['metadata']['anonymous_amount']
        anonymous_donor = subscription['plan']['metadata']['anonymous_donor']
        try:
            campaign_pk = subscription['plan']['metadata']['campaign']
            campaign = get_object_or_404(Campaign, pk=campaign_pk)
        except KeyError:
            campaign = None
        page_pk = subscription['plan']['metadata']['page']
        try:
            comment = subscription['plan']['metadata']['comment']
        except KeyError:
            comment = ''
        pf_user_pk = subscription['plan']['metadata']['pf_user_pk']

    else:
        anonymous_amount = event_json['data']['object']['metadata']['anonymous_amount']
        anonymous_donor = event_json['data']['object']['metadata']['anonymous_donor']
        try:
            campaign_pk = event_json['plan']['metadata']['campaign']
            campaign = get_object_or_404(Campaign, pk=campaign_pk)
        except KeyError:
            campaign = None
        page_pk = event_json['data']['object']['metadata']['page']
        try:
            comment = event_json['data']['object']['metadata']['comment']
        except KeyError:
            comment = ''
        pf_user_pk = event_json['data']['object']['metadata']['pf_user_pk']

    amount = event_json['data']['object']['amount']
    page = get_object_or_404(Page, pk=page_pk)
    stripe_charge_id = event_json['data']['object']['id']
    user = get_object_or_404(User, pk=pf_user_pk)

    Donation.objects.create(
        amount=amount,
        anonymous_amount=anonymous_amount,
        anonymous_donor=anonymous_donor,
        comment=comment,
        page=page,
        campaign=campaign,
        stripe_charge_id=stripe_charge_id,
        user=user
     )

    print("donation created")
    return HttpResponse(status=200)

@require_POST
@csrf_exempt
def customer_subscription_created(request):
    event_json = json.loads(request.body.decode('utf-8'))
    print("raw customer.subscription.created")
    print(json.dumps(event_json, indent=4, sort_keys=True))

    amount = event_json['data']['object']['plan']['amount']
    page_pk = event_json['data']['object']['plan']['metadata']['page']
    page = get_object_or_404(Page, pk=page_pk)
    try:
        campaign_pk = event_json['data']['object']['plan']['metadata']['campaign']
        campaign = get_object_or_404(Campaign, pk=campaign_pk)
    except KeyError:
        campaign = None
    interval = event_json['data']['object']['plan']['interval']
    pf_user_pk = event_json['data']['object']['plan']['metadata']['pf_user_pk']
    user = get_object_or_404(User, pk=pf_user_pk)
    plan = event_json['data']['object']['plan']['id']
    subscription = event_json['data']['object']['id']

    StripePlan.objects.create(
        user=user,
        amount=amount,
        page=page,
        campaign=campaign,
        interval=interval,
        stripe_plan_id=plan,
        stripe_subscription_id=subscription,
    )

    return HttpResponse(status=200)

@require_POST
@csrf_exempt
def customer_subscription_deleted(request):
    event_json = json.loads(request.body.decode('utf-8'))
    print("raw customer.subscription.deleted")
    print(json.dumps(event_json, indent=4, sort_keys=True))

    subscription_id = event_json['data']['object']['id']
    plan = get_object_or_404(StripePlan, stripe_subscription_id=subscription_id)
    plan.delete()

    return HttpResponse(status=200)