from django import forms
from django.core.validators import MaxValueValidator, MinValueValidator
from .models import Review


class ReviewForm(forms.ModelForm):
    rating = forms.ChoiceField(
        choices=[(1, "1 - Poor"), (2, "2 - Fair"), (3, "3 - Good"), (4, "4 - Very Good"), (5, "5 - Excellent")],
        widget=forms.Select(),
        label="Rating (1-5 Stars)",
    )

    class Meta:
        model = Review
        fields = ["rating", "comment"]
        widgets = {
            "comment": forms.Textarea(
                attrs={
                    "rows": 4,
                    "placeholder": "Describe your meetup experience, communication, item condition accuracy, etc.",
                }
            ),
        }

