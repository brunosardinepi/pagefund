from django import forms


class BaseDonate(forms.Form):
    anonymous_amount = forms.BooleanField(required=False)
    anonymous_donor = forms.BooleanField(required=False)
    comment = forms.CharField(widget=forms.Textarea(attrs={
        'placeholder': 'Type your comment here (optional)',
        'rows': 3,
        }), required=False)
    amount = forms.IntegerField(min_value=0, max_value=999999, required=False)

class DonateForm(BaseDonate):
    monthly = forms.BooleanField(required=False)

class DonateUnauthenticatedForm(BaseDonate):
    first_name = forms.CharField(max_length=255)
    last_name = forms.CharField(max_length=255)
