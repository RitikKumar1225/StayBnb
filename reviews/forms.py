from django import forms

from .models import Review


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ("rating", "comment")
        widgets = {
            "rating": forms.Select(choices=[(n, f"{n} / 5") for n in range(5, 0, -1)]),
            "comment": forms.Textarea(attrs={"rows": 4, "placeholder": "What made this stay memorable?"}),
        }
