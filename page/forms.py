from django import forms

from . import models


class PageForm(forms.ModelForm):
    ssn = forms.CharField(max_length=4, label="Last 4 of SSN")
    tos_acceptance = forms.BooleanField(required=True)

    class Meta:
        model = models.Page
        fields = [
            'name',
            'ein',
            'address_line1',
            'address_line2',
            'city',
            'state',
            'zipcode',
            'page_slug',
            'type',
            'nonprofit_number',
            'category',
            'description',
            'contact_email',
            'contact_phone',
            'website'
        ]

class PageImagesForm(forms.ModelForm):
    class Meta:
        model = models.PageImages
        fields = [
            'image',
            'caption',
            'page_profile'
        ]

class DeletePageForm(forms.ModelForm):
    class Meta:
        model = models.Page
        fields = ['name']

class ManagerInviteForm(forms.Form):
    email = forms.EmailField()
    manager_edit = forms.BooleanField(required=False, label='Edit Page')
    manager_delete = forms.BooleanField(required=False, label='Delete Page')
    manager_invite = forms.BooleanField(required=False, label='Invite users to manage Page')
    manager_upload = forms.BooleanField(required=False, label='Upload image')

class PageBankForm(forms.Form):
    account_holder_first_name = forms.CharField(max_length=255)
    account_holder_last_name = forms.CharField(max_length=255)
    account_number = forms.CharField(max_length=12)
    routing_number = forms.CharField(max_length=9)

class PageDonateForm(forms.Form):
    anonymous = forms.BooleanField(required=False)
    comment = forms.CharField(widget=forms.Textarea, required=False)
    amount = forms.IntegerField()
