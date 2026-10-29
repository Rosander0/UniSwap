from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from .models import Campus

User = get_user_model()


class SignUpForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(attrs={"placeholder": "Password"}), min_length=8)
    password_confirm = forms.CharField(widget=forms.PasswordInput(attrs={"placeholder": "Confirm Password"}), label="Confirm Password")

    class Meta:
        model = User
        fields = ["username", "college_email", "department", "year"]
        widgets = {
            "username": forms.TextInput(attrs={"placeholder": "Choose a username"}),
            "college_email": forms.EmailInput(attrs={"placeholder": "you@campus.edu or your email"}),
            "department": forms.TextInput(attrs={"placeholder": "e.g., Computer Science"}),
            "year": forms.TextInput(attrs={"placeholder": "e.g., Sophomore, 2026"}),
        }

    def clean_college_email(self):
        email = self.cleaned_data.get("college_email", "").strip().lower()
        if "@" not in email:
            raise ValidationError("Enter a valid email address.")
        domain = email.split("@")[-1]

        campus = Campus.objects.filter(email_domain__iexact=domain).first()
        if not campus:
            if getattr(settings, "ALLOW_ANY_EMAIL_DOMAIN", True):
                # Automatically register new campus domain so any email type is accepted
                domain_prefix = domain.split(".")[0]
                campus_name = f"{domain_prefix.upper() if len(domain_prefix) <= 4 else domain_prefix.capitalize()} Campus"
                if Campus.objects.filter(name=campus_name).exists():
                    campus_name = f"{campus_name} ({domain})"
                campus = Campus.objects.create(name=campus_name, email_domain=domain)
            else:
                raise ValidationError(
                    f"The email domain '@{domain}' is not registered with any supported campus."
                )

        if User.objects.filter(college_email__iexact=email).exists():
            raise ValidationError("An account with this college email already exists.")

        self.campus = campus
        return email

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        password_confirm = cleaned_data.get("password_confirm")

        if password and password_confirm and password != password_confirm:
            self.add_error("password_confirm", "Passwords do not match.")

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        user.email = self.cleaned_data["college_email"]
        user.campus = self.campus
        user.is_email_verified = True
        if commit:
            user.save()
        return user
