import datetime
import json
import random


fixture = []
model = "donation.Donation"
initial_date = datetime.datetime(2018, 1, 1, 0, 0, 0, 0, tzinfo=datetime.timezone.utc)
page_pks = [20]
campaign_pks = [19]
participant_pks = [27, 28, 29]
user_pks = [33, 24, 32]

for x in range(201,301):
    amount = random.randint(100,10000)
    date = initial_date + datetime.timedelta(days=random.randint(0,50))
    page = random.choice(page_pks)
    campaign = random.choice(campaign_pks)
    participant = random.choice(participant_pks)
    user = random.choice(user_pks)

    dict = {
        "model": model,
        "pk": x,
        "fields": {
            "amount": amount,
            "date": str(date),
            "page": page,
            "campaign": campaign,
            "campaign_participant": participant,
            "user": user,
        }
    }

    fixture.append(dict)

fixture = json.dumps(fixture)
with open("/home/pfadmin/pagefund/donation/fixtures/donation_fixtures_campaign_vote.json", 'w') as f:
    f.write(str(fixture))