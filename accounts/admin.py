from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import Campus, User


@admin.register(Campus)
class CampusAdmin(admin.ModelAdmin):
    list_display = ("name", "email_domain")
    search_fields = ("name", "email_domain")


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = (
        "username",
        "college_email",
        "campus",
        "department",
        "year",
        "is_email_verified",
        "is_staff",
    )
    list_filter = ("is_email_verified", "campus", "is_staff", "is_superuser")
    search_fields = ("username", "college_email", "department")
    fieldsets = BaseUserAdmin.fieldsets + (
        (
            "Campus Details",
            {
                "fields": (
                    "college_email",
                    "is_email_verified",
                    "campus",
                    "department",
                    "year",
                )
            },
        ),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        (
            "Campus Details",
            {
                "fields": (
                    "college_email",
                    "is_email_verified",
                    "campus",
                    "department",
                    "year",
                )
            },
        ),
    )
