from django.shortcuts import get_object_or_404

import stripe

from . import models
from donation.models import Donation
from pagefund import settings


def get_user_credit_cards(userprofile):
    cards = {}
    if not settings.TESTING:
        try:
            sc = stripe.Customer.retrieve(userprofile.stripe_customer_id).sources.all(object='card')
            for c in sc:
                card = get_object_or_404(models.StripeCard, stripe_card_id=c.id)
                cards[card.id] = {
                    'exp_month': c.exp_month,
                    'exp_year': c.exp_year,
                    'name': card.name,
                    'id': card.id,
                    'last4': c.last4,
                    'default': card.default
                }
        except stripe.error.InvalidRequestError as e:
            metadata = {'user_pk': userprofile.user.pk}
            customer = stripe.Customer.create(
                email=userprofile.user.email,
                metadata=metadata
            )

            userprofile.stripe_customer_id = customer.id
            userprofile.save()
    return cards

def get_last4_donation(donation):
    if not settings.TESTING:
        try:
            charge = stripe.Charge.retrieve(donation.stripe_charge_id)
            return charge["source"]["last4"]
        except:
            pass
