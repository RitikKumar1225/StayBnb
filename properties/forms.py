from django import forms

from .models import Property


class PropertyForm(forms.ModelForm):
    class Meta:
        model = Property
        fields = ("title", "description", "location", "property_type", "price_per_night", "cover_image", "amenities")
        labels = {
            "price_per_night": "Price per night (USD)",
            "cover_image": "Cover photo (optional)",
        }
        widgets = {
            "description": forms.Textarea(attrs={"rows": 5}),
            "amenities": forms.TextInput(attrs={"placeholder": "Wifi, Kitchen, Garden"}),
            "price_per_night": forms.NumberInput(attrs={"min": "1", "step": "0.01"}),
            "cover_image": forms.FileInput(attrs={"accept": "image/*"}),
        }


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleImageField(forms.ImageField):
    widget = MultipleFileInput

    def clean(self, data, initial=None):
        if not data:
            return []
        files = data if isinstance(data, (list, tuple)) else [data]
        return [super(MultipleImageField, self).clean(item, initial) for item in files]


class PropertyImageUploadForm(forms.Form):
    images = MultipleImageField(required=False, widget=MultipleFileInput(attrs={"accept": "image/*"}))


class PropertySearchForm(forms.Form):
    location = forms.CharField(required=False, max_length=180)
    type = forms.ChoiceField(required=False, choices=[("", "Any kind of stay"), *Property.TYPE_CHOICES])
    min_price = forms.DecimalField(required=False, min_value=0)
    max_price = forms.DecimalField(required=False, min_value=0)

    def clean(self):
        cleaned = super().clean()
        minimum = cleaned.get("min_price")
        maximum = cleaned.get("max_price")
        if minimum is not None and maximum is not None and maximum < minimum:
            self.add_error("max_price", "Maximum price must be at least the minimum price.")
        return cleaned
