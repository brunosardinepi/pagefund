# PageFund

### Prerequisites

```
pagefund/config.py
```

```
pip install -r requirements.txt
```

```
crontab -e
0 * * * * /home/[user]/pagefund/pagefundenv/bin/python3 /home/[user]/pagefund/pagefund/trending_pages.py
0 * * * * /home/[user]/pagefund/pagefundenv/bin/python3 /home/[user]/pagefund/pagefund/trending_campaigns.py
* * * * * /home/[user]/pagefund/pagefundenv/bin/python3 /home/[user]/pagefund/manage.py campaign_end
0 * * * * /home/[user]/pagefund/pagefundenv/bin/python3 /home/[user]/pagefund/manage.py invitation_expire
*/2 * * * * /home/[user]/pagefund/pagefundenv/bin/python3 /home/[user]/pagefund/manage.py page_verification_check
```

&copy; 2017 PageFund, Inc.
