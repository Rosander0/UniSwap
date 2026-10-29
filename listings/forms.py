from django import forms
from django.forms import inlineformset_factory
from .models import Listing, ListingImage


class ListingForm(forms.ModelForm):
    class Meta:
        model = Listing
        fields = ["title", "category", "price", "condition", "description"]
        widgets = {
            "title": forms.TextInput(attrs={"placeholder": "e.g., Organic Chemistry 8th Edition (Vollhardt)"}),
            "price": forms.NumberInput(attrs={"placeholder": "0.00", "step": "0.01", "min": "0"}),
            "description": forms.Textarea(attrs={"rows": 4, "placeholder": "Describe condition, course number, included accessories, etc."}),
            "condition": forms.Select(),
            "category": forms.Select(),
        }


ListingImageFormSet = inlineformset_factory(
    Listing,
    ListingImage,
    fields=["image"],
    extra=3,
    can_delete=True,
    widgets={"image": forms.ClearableFileInput(attrs={"accept": "image/*"})},
)

