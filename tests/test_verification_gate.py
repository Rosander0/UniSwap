from decimal import Decimal
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from accounts.models import Campus
from listings.models import Category, Listing

User = get_user_model()


@override_settings(REQUIRE_EMAIL_VERIFICATION=True)
class VerificationGateTests(TestCase):
    def setUp(self):
        self.campus = Campus.objects.create(name="Tech Institute", email_domain="tech.edu")
        self.verified_user = User.objects.create_user(
            username="verified_user",
            college_email="verified@tech.edu",
            password="Password123!",
            is_email_verified=True,
            campus=self.campus,
        )
        self.unverified_user = User.objects.create_user(
            username="unverified_user",
            college_email="unverified@tech.edu",
            password="Password123!",
            is_email_verified=False,
            campus=self.campus,
        )
        self.category, _ = Category.objects.get_or_create(slug="textbooks", defaults={"name": "Textbooks"})
        self.listing = Listing.objects.create(
            seller=self.verified_user,
            campus=self.campus,
            category=self.category,
            title="Calculus Vol 1",
            description="Good condition",
            price=Decimal("40.00"),
            condition="Good",
            status="Active",
        )

    def test_unverified_user_cannot_browse_listings(self):
        self.client.login(username="unverified_user", password="Password123!")
        response = self.client.get(reverse("listings:list"))
        self.assertRedirects(response, reverse("accounts:verify_notice"))

    def test_unverified_user_cannot_view_listing_details(self):
        self.client.login(username="unverified_user", password="Password123!")
        response = self.client.get(reverse("listings:detail", kwargs={"id": self.listing.id}))
        self.assertRedirects(response, reverse("accounts:verify_notice"))

    def test_unverified_user_cannot_create_listing(self):
        self.client.login(username="unverified_user", password="Password123!")
        response = self.client.get(reverse("listings:create"))
        self.assertRedirects(response, reverse("accounts:verify_notice"))

    def test_unverified_user_cannot_access_messages(self):
        self.client.login(username="unverified_user", password="Password123!")
        response = self.client.get(reverse("messaging:inbox"))
        self.assertRedirects(response, reverse("accounts:verify_notice"))

    def test_unverified_user_cannot_view_profiles(self):
        self.client.login(username="unverified_user", password="Password123!")
        response = self.client.get(reverse("user_profile", kwargs={"pk": self.verified_user.pk}))
        self.assertRedirects(response, reverse("accounts:verify_notice"))

    def test_unauthenticated_user_redirected_to_login(self):
        response = self.client.get(reverse("listings:list"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("accounts:login"), response.url)
