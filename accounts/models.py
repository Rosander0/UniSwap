from django.contrib.auth.models import AbstractUser
from django.db import models


class Campus(models.Model):
    name = models.CharField(max_length=150, unique=True)
    email_domain = models.CharField(
        max_length=100,
        unique=True,
        help_text="Campus email domain (e.g., campus.edu, stanford.edu)",
    )

    class Meta:
        verbose_name_plural = "Campuses"
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} (@{self.email_domain})"


class User(AbstractUser):
    college_email = models.EmailField(
        unique=True,
        help_text="Institutional email address required for campus verification",
    )
    is_email_verified = models.BooleanField(
        default=False,
        help_text="Indicates whether the user has verified their college email",
    )
    campus = models.ForeignKey(
        Campus,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="users",
    )
    department = models.CharField(max_length=100, blank=True)
    year = models.CharField(max_length=20, blank=True)

    def __str__(self):
        return self.username or self.college_email
