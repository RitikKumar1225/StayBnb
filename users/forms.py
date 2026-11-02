from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import Profile

class SignUpForm(UserCreationForm):
    email = forms.EmailField()
    first_name = forms.CharField(max_length=150, label="Your name")
    class Meta:
        model = User
        fields = ("first_name", "username", "email", "password1", "password2")

    def save(self, commit=True):
        user = super().save(commit=False)
        user.first_name = self.cleaned_data["first_name"]
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
            Profile.objects.get_or_create(user=user)
        return user


class ProfileForm(forms.ModelForm):
    first_name = forms.CharField(max_length=150, label="Your name")
    email = forms.EmailField()

    class Meta:
        model = Profile
        fields = ("bio",)
        widgets = {"bio": forms.Textarea(attrs={"rows": 3})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["first_name"].initial = self.instance.user.first_name
        self.fields["email"].initial = self.instance.user.email

    def save(self, commit=True):
        profile = super().save(commit=commit)
        profile.user.first_name = self.cleaned_data["first_name"]
        profile.user.email = self.cleaned_data["email"]
        if commit:
            profile.user.save()
        return profile
