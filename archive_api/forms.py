from datetime import date

from django import forms
from django.utils import timezone

from archive_api.models import ServiceAccount, SERVICE_ACCOUNT_CHOICES


class MetricsFilterForm(forms.Form):
    start_date = forms.DateField(label='Start Date',
                                 widget=forms.DateInput(attrs={'maxlength': 10}),
                                 initial=date(year=2016, month=1, day=1),
                                 required=True,
                                 help_text="Filter the metrics on or after this date.")
    end_date = forms.DateField(label='End Date', widget=forms.DateInput(attrs={'maxlength': 10}),
                               initial=timezone.now(),
                               required=True,
                               help_text="Filter metrics before this date.")


class ServiceAccountForm(forms.ModelForm):
    name = forms.CharField(label='Service Name', required=True, widget=forms.TextInput({'size': 40}))
    service = forms.ChoiceField(label='Service', required=True, choices=SERVICE_ACCOUNT_CHOICES)
    identity = forms.CharField(label='Account Identity', required=False, widget=forms.TextInput({'size': 40}))
    secret = forms.CharField(label='Account Secret',
                             required=True, widget=forms.PasswordInput(
            attrs={'placeholder': '********', 'autocomplete': 'off', 'data-toggle': 'password', 'size': 50}),
                             max_length=1000)
    endpoint = forms.CharField(label="Service URL", required=True, widget=forms.URLInput(attrs={'size': 50}), )

    class Meta:
        model = ServiceAccount
        fields = '__all__'
