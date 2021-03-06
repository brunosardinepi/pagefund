import json
import operator

from datetime import timezone
from time import strftime

from collections import OrderedDict
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models.functions import Lower
from django.db.models import Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.http import Http404, HttpResponse, HttpResponseRedirect, JsonResponse
from django.urls import reverse
from django.utils import timezone
from django.views import View

import stripe
from formtools.wizard.views import SessionWizardView
from guardian.shortcuts import assign_perm, get_user_perms, remove_perm

from . import forms
from .models import Page, PageImage
from .utils import campaign_average_duration, campaign_success_pct, campaign_types
from campaign.models import Campaign
from comments.forms import CommentForm
from donation.forms import DonateForm, DonateUnauthenticatedForm
from donation.models import Donation
from donation.utils import donate, donation_graph, donation_history, donation_statistics
from notes.utils import create_error
from invitations.models import ManagerInvitation
from invitations.utils import invite
from userprofile.models import UserProfile
from userprofile.utils import get_user_credit_cards
from pagefund import config, settings, utils
from pagefund.image import image_is_valid
from plans.models import StripePlan


stripe.api_key = config.settings['stripe_api_sk']

TEMPLATES = {"Organization": "page/page_create_business.html",
             "Personal": "page/page_create_personal.html",
             "EIN": "page/page_create_ein.html",
             "Bank": "page/page_create_account.html",
             "Review": "page/page_create_review.html"}

def stripe_unverified(request, page):
    if request.user.is_authenticated():
        if request.user.userprofile in page.admins.all() or request.user.userprofile in page.managers.all():
            return redirect('page_edit_bank_info', page_slug=page.page_slug)
        else:
            return redirect('notes:error_page_does_not_exist')
    else:
        return redirect('notes:error_page_does_not_exist')

def page(request, page_slug):
    try:
        page = Page.objects.get(page_slug=page_slug)
    except Page.DoesNotExist:
        return redirect('notes:error_page_does_not_exist')

    if page.deleted == False:
        if page.stripe_verified == True:
            template_params = {}
            if request.user.is_authenticated():
                donate_form = DonateForm()
                template_params["form"] = CommentForm
            else:
                donate_form = DonateUnauthenticatedForm()

            try:
                user_subscription_check = page.subscribers.get(user_id=request.user.pk)
            except UserProfile.DoesNotExist:
                user_subscription_check = None

            if user_subscription_check:
                subscribed = True
            else:
                subscribed = False

            template_params["page"] = page
            template_params["donate_form"] = donate_form
            template_params["subscribed"] = subscribed
            template_params["api_pk"] = config.settings['stripe_api_pk']
            return render(request, 'page/page.html', template_params)
        else:
            return stripe_unverified(request, page)
    else:
        return redirect('notes:error_page_does_not_exist')

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def show_message_form_condition(wizard):
    # try to get the cleaned data of step 0
    cleaned_data = wizard.get_cleaned_data_for_step('Organization') or {}
    # check if type is nonprofit
    return cleaned_data.get('type') == 'nonprofit'

class PageWizard(SessionWizardView):
    def get_context_data(self, form, **kwargs):
        context = super(PageWizard, self).get_context_data(form=form, **kwargs)
        if self.steps.current == 'Review':
            context.update({'all_data': self.get_all_cleaned_data()})
        return context

    def get_template_names(self):
        return [TEMPLATES[self.steps.current]]

    def done(self, form_list, **kwargs):
        # put the form results into a dict
        form = self.get_all_cleaned_data()

        # make the Page object but don't save it
        # until we make the stripe transaction
        page = Page(
            address_line1 = form['address_line1'],
            address_line2 = form['address_line2'],
            city = form['city'],
            description = form['description'],
            name = form['name'],
            stripe_account_id = '',
            stripe_bank_account_id = '',
            tos_accepted = form['tos_accepted'],
            zipcode = form['zipcode'],
            category = form['category'],
            state = form['state'],
            type = form['type'],
        )

        # only make the stripe account if we're live
        if not settings.TESTING:

            # create stripe data for the account
            legal_entity = {
                "business_name": page.name,
                "address": {
                    "city": page.city,
                    "line1": page.address_line1,
                    "line2": page.address_line2,
                    "postal_code": page.zipcode,
                    "state": page.state
                },
                'ssn_last_4': form['ssn'],
                'first_name': form['first_name'],
                'last_name': form['last_name'],
                "dob": {
                    "day": form['birthday'].day,
                    "month": form['birthday'].month,
                    "year": form['birthday'].year,
                },
            }

            # set the stripe type based on page type
            if page.type == 'nonprofit':
                stripe_type = 'company'
                legal_entity['business_tax_id'] = form['ein']
            else:
                stripe_type = 'individual'

            legal_entity["type"] = stripe_type

            user_ip = get_client_ip(self.request)
            tos_acceptance = {
                "date": timezone.now(),
                "ip": user_ip
            }

            payout_schedule = {
                'delay_days': 'minimum',
                'interval': 'weekly',
                'weekly_anchor': 'monday',
            }

            # create the stripe account
            # and save the page if all goes well
            try:
                account = stripe.Account.create(
                    business_name=page.name,
                    country="US",
                    email=self.request.user.email,
                    legal_entity=legal_entity,
                    type="custom",
                    tos_acceptance=tos_acceptance,
                    payout_schedule=payout_schedule,
                    statement_descriptor='PageFund',
                )

                external_account = {
                    "object": "bank_account",
                    "country": "US",
                    "account_number": form['account_number'],
                    "account_holder_name": "{} {}".format(form['first_name'], form['last_name']),
                    "account_holder_type": stripe_type,
                    "routing_number": form['routing_number'],
                    "default_for_currency": "true",
                }
                ext_account = account.external_accounts.create(external_account=external_account)

                page.stripe_account_id = account.id
                page.stripe_bank_account_id = ext_account.id

                # give them the benefit of the doubt and let them accept donations right away
                # it'll get fixed within 2 minutes if it's unverified
                page.stripe_verified = True

                # stripe processed it so we can save the page now
                page.save()

                # update the stripe metadata for the url
                metadata = {
                    'url': 'https://page.fund/{}/'.format(page.page_slug),
                }
                account.metadata = metadata
                account.save()

                # add the user as an admin and subscriber
                page.admins.add(self.request.user.userprofile)
                page.subscribers.add(self.request.user.userprofile)

            # catch stripe exceptions
            # and alert the user and me about it
            # note that the page doesn't get created if this happens
            except stripe.error.InvalidRequestError as e:
                create_error(e, self.request)
                return redirect('notes:error_stripe_invalid_request')

            # send emails
            # placed outside of stripe try block because it's ok if these fail
            try:
                substitutions = {
                    "-pagename-": page.name,
                }
                utils.email(self.request.user.email, "blank", "blank", "new_page_created", substitutions)

                date = timezone.now().strftime("%Y-%m-%d %I:%M:%S %Z")
                utils.email("gn9012@gmail.com", "blank", "blank", "admin_new_page", {
                    '-user-': self.request.user.email,
                    '-page-': page.name,
                    '-date-': date,
                })
            except:
                pass

        # so tests will pass
        else:
            page.save()
            # add the user as an admin and subscriber
            page.admins.add(self.request.user.userprofile)
            page.subscribers.add(self.request.user.userprofile)

        return HttpResponseRedirect(page.get_absolute_url())

class PageEditBankInfo(View):
    def get(self, request, page_slug):
        page = get_object_or_404(Page, page_slug=page_slug)
        if page.type == 'nonprofit':
            if page.stripe_verified == True:
                form = forms.PageEditBankEINForm()
            else:
                form = forms.PageUnverifiedEditBankEINForm()
        else:
            if page.stripe_verified == True:
                form = forms.PageEditBankForm()
            else:
                form = forms.PageUnverifiedEditBankForm()
        if page.deleted == False:
            if utils.has_dashboard_access(request.user, page, 'manager_edit'):
                if page.stripe_verified == True:
                    return render(request, 'page/page_edit_bank_info.html', {'page': page, 'form': form})
                else:
                    return render(request, 'page/page_unverified_edit_bank_info.html', {'page': page, 'form': form})
            else:
                return redirect('notes:error_permissions')
        else:
            return redirect('notes:error_page_does_not_exist')

    def post(self, request, page_slug):
        page = get_object_or_404(Page, page_slug=page_slug)
        # if the page is a nonprofit,
        # we need their EIN
        if page.type == 'nonprofit':
            if page.stripe_verified == True:
                form = forms.PageEditBankEINForm(request.POST)
            else:
                form = forms.PageUnverifiedEditBankEINForm(request.POST)
        else:
            if page.stripe_verified == True:
                form = forms.PageEditBankForm(request.POST)
            else:
                form = forms.PageUnverifiedEditBankForm(request.POST)
        if page.deleted == False:
            if utils.has_dashboard_access(request.user, page, 'manager_edit'):
                if form.is_valid():
                    if not settings.TESTING:

                        # set the stripe type to determine if we need EIN
                        if page.type == 'nonprofit':
                            stripe_type = 'company'
                        else:
                            stripe_type = 'individual'

                        # retrieve account from stripe
                        account = stripe.Account.retrieve(page.stripe_account_id)
                        # update stripe information
                        if page.stripe_verified == True:
                            if account['legal_entity']['ssn_last_4_provided'] == False:
                                account.legal_entity.ssn_last_4 = form.cleaned_data['ssn']
                        else:
                            account.legal_entity.personal_id_number = form.cleaned_data['ssn']
                        if page.type == 'nonprofit':
                            account.legal_entity.business_tax_id = form.cleaned_data['ein']

                        # save the account or redirect for an exception
                        try:
                            account.save()
                        except stripe.error.InvalidRequestError as e:
                            print("e = {}".format(e))
                            error = create_error(e, request)
                            return redirect('notes:error_stripe_invalid_request')

                        # create the bank account
                        external_account = {
                            'object': 'bank_account',
                            'country': 'US',
                            'currency': 'usd',
                            'account_number': form.cleaned_data['account_number'],
                            'account_holder_type': stripe_type,
                            'routing_number': form.cleaned_data['routing_number'],
                            'default_for_currency': 'true',
                        }
                        try:
                            ext_account = account.external_accounts.create(external_account=external_account)
                        except Exception as e:
                            print("exception = {}".format(e))

                        # delete the old account here
                        # so that we can set the new one as default first
                        try:
                            account.external_accounts.retrieve(page.stripe_bank_account_id).delete()
                        except:
                            pass

                        page.stripe_bank_account_id = ext_account.id
                    page.save()

                    # email the user
                    substitutions = {
                        "-pagename-": page.name,
                    }
                    utils.email(request.user.email, "blank", "blank", "page_bank_information_updated", substitutions)
                    # add message
                    messages.success(request, 'Bank information updated', fail_silently=True)
                    return redirect('page_dashboard_admin', page_slug=page.page_slug)
            else:
                return redirect('notes:error_permissions')
        else:
            return redirect('notes:error_page_does_not_exist')

@login_required
def page_edit(request, page_slug):
    page = get_object_or_404(Page, page_slug=page_slug)

    if page.deleted == False:
        if page.stripe_verified == True:
            if utils.has_dashboard_access(request.user, page, 'manager_edit'):
                form = forms.PageEditForm(instance=page)
                if request.method == 'POST':
                    form = forms.PageEditForm(instance=page, data=request.POST)
                    if form.is_valid():
                        if 'page_slug' in form.changed_data:
                            # update the stripe metadata for the url
                            metadata = {
                                'url': 'https://page.fund/{}/'.format(form.cleaned_data['page_slug']),
                            }
                            account = stripe.Account.retrieve(page.stripe_account_id)
                            account.metadata = metadata
                            account.save()
                        form.save()
                        messages.success(request, 'Page updated', fail_silently=True)
                        return redirect('page_dashboard_admin', page_slug=page.page_slug)
            else:
                return redirect('notes:error_permissions')
        else:
            return stripe_unverified(request, page)
    else:
        return redirect('notes:error_page_does_not_exist')

    return render(request, 'page/page_edit.html', {'page': page, 'form': form})

@login_required
def page_delete(request, page_slug):
    page = get_object_or_404(Page, page_slug=page_slug)

    if page.deleted == False:
        if page.stripe_verified == True:
            if utils.has_dashboard_access(request.user, page, 'manager_delete'):
                page.deleted = True
                page.deleted_by = request.user
                page.deleted_on = timezone.now()
                page.name = page.name + "_deleted_" + timezone.now().strftime("%Y%m%d")
                page.page_slug = page.page_slug + "deleted" + timezone.now().strftime("%Y%m%d")
                page.save()

                campaigns = Campaign.objects.filter(page=page, deleted=False)
                if campaigns:
                    for c in campaigns:
                        c.deleted = True
                        c.deleted_by = request.user
                        c.deleted_on = timezone.now()
                        c.name = c.name + "_deleted_" + timezone.now().strftime("%Y%m%d")
                        c.campaign_slug = c.campaign_slug + "deleted" + timezone.now().strftime("%Y%m%d")
                        c.save()

                if not settings.TESTING:
                    try:
                        account = stripe.Account.retrieve(page.stripe_account_id)
                        account.delete()
                    except stripe.error.InvalidRequestError:
                        pass

                return HttpResponseRedirect(reverse('home'))
            else:
                return redirect('notes:error_permissions')
        else:
            return stripe_unverified(request, page)
    else:
        return redirect('notes:error_page_does_not_exist')

@login_required
def subscribe(request, page_pk, action=None):
    page = get_object_or_404(Page, pk=page_pk)

    if request.user.userprofile in page.subscribers.all():
        page.subscribers.remove(request.user.userprofile)
        messages.success(request, 'You are now unsubscribed from this Page', fail_silently=True)
    else:
        page.subscribers.add(request.user.userprofile)
        messages.success(request, 'You are now subscribed to this Page', fail_silently=True)

    return HttpResponseRedirect(page.get_absolute_url())

@login_required
def page_invite(request, page_slug):
    page = get_object_or_404(Page, page_slug=page_slug)

    if page.deleted == False:
        if page.stripe_verified == True:
            if utils.has_dashboard_access(request.user, page, 'manager_invite'):
                form = forms.ManagerInviteForm()
                if request.method == 'POST':
                    form = forms.ManagerInviteForm(request.POST)
                    if form.is_valid():
                        # check if the person we are inviting is already a manager/admin
                        try:
                            user = User.objects.get(email=form.cleaned_data['email'])
                            if user.userprofile in page.admins.all() or user.userprofile in page.managers.all():
                                return redirect('notes:error_invite_manager_exists')
                        except User.DoesNotExist:
                            pass
                        data = {
                            "request": request,
                            "form": form,
                            "page": page,
                            "campaign": None
                        }
                        status = invite(data)
                        if status == True:
                            messages.success(request, 'Invitation sent', fail_silently=True)
                            # redirect the admin/manager to the Page
                            return redirect('page_dashboard_admin', page_slug=page.page_slug)
                return render(request, 'page/page_invite.html', {'form': form, 'page': page})
            # the user isn't an admin or a manager, so they can't invite someone
            # the only way someone got here was by typing the url manually
            else:
                return redirect('notes:error_permissions')
        else:
            return stripe_unverified(request, page)
    else:
        return redirect('notes:error_page_does_not_exist')

@login_required
def remove_manager(request, page_slug, manager_pk):
    page = get_object_or_404(Page, page_slug=page_slug)
    manager = get_object_or_404(User, pk=manager_pk)

    if page.deleted == False:
        if page.stripe_verified == True:
            # only page admins can remove managers
            if request.user.userprofile in page.admins.all() or manager == request.user:
                # remove the manager
                page.managers.remove(manager.userprofile)
                # revoke the permissions
                remove_perm('manager_edit', manager, page)
                remove_perm('manager_delete', manager, page)
                remove_perm('manager_invite', manager, page)
                remove_perm('manager_image_edit', manager, page)
                remove_perm('manager_view_dashboard', manager, page)
                messages.success(request, 'Manager removed', fail_silently=True)
                # redirect to page admin
                return redirect('page_dashboard_admin', page_slug=page.page_slug)
            else:
                return redirect('notes:error_permissions')
        else:
            return stripe_unverified(request, page)
    else:
        return redirect('notes:error_page_does_not_exist')

class PageDonate(View):
    def get(self, request, page_slug):
        template_params = {}
        page = get_object_or_404(Page, page_slug=page_slug)

        if request.user.is_authenticated():
            form = DonateForm()
            try:
                cards = get_user_credit_cards(request.user.userprofile)
                template_params["cards"] = cards
            except Exception as e:
                template_params["stripe_error"] = True
                create_error(e, request)
        else:
            form = DonateUnauthenticatedForm()

        template_params["page"] = page
        template_params["form"] = form
        template_params["api_pk"] = config.settings['stripe_api_pk']

        return render(self.request, 'page/page_donate.html', template_params)

    def post(self, request, page_slug):
        page = get_object_or_404(Page, page_slug=page_slug)

        if request.user.is_authenticated():
            form = DonateForm(request.POST)
        else:
            form = DonateUnauthenticatedForm(request.POST)
        if form.is_valid():
            donate(request=request, form=form, page=page, campaign=None)
            messages.success(request, 'Donation successful', fail_silently=True)
            return HttpResponseRedirect(page.get_absolute_url())

@login_required
def page_image_delete(request, image_pk):
    image = get_object_or_404(PageImage, pk=image_pk)
    if utils.has_dashboard_access(request.user, image.page, 'manager_image_edit'):
        image.delete()
        return HttpResponse('')
    else:
        return redirect('notes:error_permissions')

@login_required
def page_profile_update(request, image_pk):
    image = get_object_or_404(PageImage, pk=image_pk)
    if utils.has_dashboard_access(request.user, image.page, 'manager_image_edit'):
        try:
            profile_picture = PageImage.objects.get(page=image.page, profile_picture=True)
        except PageImage.DoesNotExist:
            profile_picture = None
        if profile_picture:
            profile_picture.profile_picture = False
            profile_picture.save()
        image.profile_picture = True
        image.save()
        return HttpResponse('')
    else:
        return redirect('notes:error_permissions')

class PageAjaxDonations(View):
    def post(self, request):
        page = get_object_or_404(Page, pk=request.POST.get("page_pk"))
        sort_by = request.POST.get("sort_by")
        column = request.POST.get("column")
        column = column.split("sort-")[1]
        donationset = Donation.objects.filter(page=page)
        data = OrderedDict()
        for d in donationset:
            d.date = d.date.replace(tzinfo=timezone.utc).astimezone(tz=None)
            data["pk{}".format(d.pk)] = {
                "date": d.date.strftime("%b. %-d, %Y, %-I:%M %p"),
                "anonymous_amount": d.anonymous_amount,
                "anonymous_donor": d.anonymous_donor,
                "user": {
                    "first_name": d.donor_first_name,
                    "last_name": d.donor_last_name,
                },
            }
            if d.anonymous_amount is True:
               data["pk{}".format(d.pk)]["amount"] = 0
            else:
                data["pk{}".format(d.pk)]["amount"] = d.amount
            if d.anonymous_donor is True:
                data["pk{}".format(d.pk)]["user"]["first_name"] = ""
                data["pk{}".format(d.pk)]["user"]["last_name"] = ""
            if d.campaign:
                data["pk{}".format(d.pk)]["campaign"] = d.campaign.name
            else:
                data["pk{}".format(d.pk)]["campaign"] = ""
        if sort_by == "asc":
            if column == "donor_first_name":
                data = sorted(data.values(), key=lambda x: (x['user']['first_name'].lower()), reverse=True)
            else:
                data = sorted(data.values(), key=operator.itemgetter('{}'.format(column)), reverse=True)
        else:
            if column == "donor_first_name":
                data = sorted(data.values(), key=lambda x: (x['user']['first_name']).lower())
            else:
                data = sorted(data.values(), key=operator.itemgetter('{}'.format(column)))
        return HttpResponse(json.dumps(data), content_type="application/json")

class PageDashboardAnalytics(View):
    def get(self, request, page_slug):
        page = get_object_or_404(Page, page_slug=page_slug)
        if page.deleted == False:
            if page.stripe_verified == True:
                if utils.has_dashboard_access(request.user, page, 'manager_view_dashboard'):
                    graph = donation_graph(page, 30)
                    graph_dates = []
                    graph_donations = []
                    for k, v in graph.items():
                        graph_dates.append(k.strftime('%b %-d'))
                        graph_donations.append(int(v/100))
                    graph_dates = list(reversed(graph_dates))
                    graph_donations = list(reversed(graph_donations))
                    return render(self.request, 'page/dashboard_analytics.html', {
                        'page': page,
                        'donations': donation_statistics(page),
                        'graph_dates': graph_dates,
                        'graph_donations': graph_donations,
                    })
                else:
                    return redirect('notes:error_permissions')
            else:
                return stripe_unverified(request, page)
        else:
            return redirect('notes:error_page_does_not_exist')

class PageDashboardAdmin(View):
    def get(self, request, page_slug):
        page = get_object_or_404(Page, page_slug=page_slug)
        if page.deleted == False:
            if page.stripe_verified == True:
                invitations = ManagerInvitation.objects.filter(page=page, expired=False)
                if utils.has_dashboard_access(request.user, page, None):
                    return render(self.request, 'page/dashboard_admin.html', {
                        'page': page,
                        'invitations': invitations,
                    })
                else:
                    return redirect('notes:error_permissions')
            else:
                return stripe_unverified(request, page)
        else:
            return redirect('notes:error_page_does_not_exist')

    def post(self, request, page_slug):
        page = get_object_or_404(Page, page_slug=page_slug)
        utils.update_manager_permissions(request.POST.getlist('permissions[]'), page)
        messages.success(request, 'Permissions updated', fail_silently=True)
        return redirect('page_dashboard_admin', page_slug=page.page_slug)

class PageDashboardDonations(View):
    def get(self, request, page_slug):
        page = get_object_or_404(Page, page_slug=page_slug)
        if page.deleted == False:
            if page.stripe_verified == True:
                if utils.has_dashboard_access(request.user, page, 'manager_view_dashboard'):
                    return render(self.request, 'page/dashboard_donations.html', {
                        'page': page,
                        'donations': donation_statistics(page),
                    })
                else:
                    return redirect('notes:error_permissions')
            else:
                return stripe_unverified(request, page)
        else:
            return redirect('notes:error_page_does_not_exist')

class PageDashboardCampaigns(View):
    def get(self, request, page_slug):
        page = get_object_or_404(Page, page_slug=page_slug)
        if page.deleted == False:
            if page.stripe_verified == True:
                if utils.has_dashboard_access(request.user, page, 'manager_view_dashboard'):
                    return render(self.request, 'page/dashboard_campaigns.html', {
                        'page': page,
                        'donations': donation_statistics(page),
                        'campaign_types': campaign_types(page),
                        'campaign_average_duration': campaign_average_duration(page),
                        'campaign_success_pct': campaign_success_pct(page),
                    })
                else:
                    return redirect('notes:error_permissions')
            else:
                return stripe_unverified(request, page)
        else:
            return redirect('notes:error_page_does_not_exist')

class PageDashboardImages(View):
    def get(self, request, page_slug):
        page = get_object_or_404(Page, page_slug=page_slug)
        if page.deleted == False:
            if page.stripe_verified == True:
                if utils.has_dashboard_access(request.user, page, 'manager_image_edit'):
                    images = PageImage.objects.filter(page=page)
                    return render(self.request, 'page/dashboard_images.html', {
                        'page': page,
                        'images': images,
                    })
                else:
                    return redirect('notes:error_permissions')
            else:
                return stripe_unverified(request, page)
        else:
            return redirect('notes:error_page_does_not_exist')

    def post(self, request, page_slug):
        page = get_object_or_404(Page, page_slug=page_slug)
        if utils.has_dashboard_access(request.user, page, 'manager_image_edit'):
            form = forms.PageImageForm(self.request.POST, self.request.FILES)
            data = image_is_valid(request, form, page)
            if data:
                return JsonResponse(data)
            else:
                return HttpResponse('')
        else:
            return redirect('notes:error_permissions')

class PageCampaigns(View):
    def get(self, request, page_slug):
        page = get_object_or_404(Page, page_slug=page_slug)
        if page.deleted == False:
            campaigns = Campaign.objects.filter(page=page, is_active=True, deleted=False).order_by('end_date')
            return render(self.request, 'page/page_campaigns_all.html', {
                'page': page,
                'campaigns': campaigns,
            })
        else:
            return redirect('notes:error_page_does_not_exist')

class PageDonations(View):
    def get(self, request, page_slug):
        page = get_object_or_404(Page, page_slug=page_slug)
        if page.deleted == False:
            donations = Donation.objects.filter(page=page).order_by('-date')
            return render(self.request, 'page/page_donations_all.html', {
                'page': page,
                'donations': donations,
            })
        else:
            return redirect('notes:error_page_does_not_exist')