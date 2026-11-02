from django import forms
from django.utils import timezone


class BookingForm(forms.Form):
    check_in = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}))
    check_out = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}))
    guests = forms.IntegerField(min_value=1, max_value=20, initial=1)

    def clean(self):
        cleaned = super().clean()
        check_in = cleaned.get("check_in")
        check_out = cleaned.get("check_out")
        if check_in and check_in < timezone.localdate():
            self.add_error("check_in", "Check-in must be today or later.")
        if check_in and check_out and check_out <= check_in:
            self.add_error("check_out", "Check-out must be after check-in.")
        return cleaned
