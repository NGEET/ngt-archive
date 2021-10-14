from datetime import date

from django import forms
from django.utils import timezone


class MetricsFilterForm(forms.Form):
    start_date = forms.DateField(label='Start Date',
                                 widget=forms.DateInput(attrs={'maxlength': 10}), initial=date(year=2016, month=1, day=1),
                                 required=True)
    end_date = forms.DateField(label='End Date', widget=forms.DateInput(attrs={'maxlength': 10}), initial=timezone.now(),
                               required=True)



