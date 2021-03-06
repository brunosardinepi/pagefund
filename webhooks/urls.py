from django.conf.urls import url

from . import views


app_name = 'webhooks'
urlpatterns = [
    url(r'^charge-succeeded/$', views.charge_succeeded, name='charge_succeeded'),
    url(r'^customer-subscription-created/$', views.customer_subscription_created, name='customer_subscription_created'),
    url(r'^customer-subscription-deleted/$', views.customer_subscription_deleted, name='customer_subscription_deleted'),
    url(r'^plan-deleted/$', views.plan_deleted, name='plan_deleted'),
    url(r'^test/$', views.webhooks_test, name='webhooks_test'),
    url(r'^all/$', views.webhooks_all,  name='webhooks_all'),
]

