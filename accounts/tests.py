from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse
from accounts.models import Campus
from accounts.tokens import generate_verification_token, verify_token

User = get_user_model()


@override_settings(REQUIRE_EMAIL_VERIFICATION=True)
class AccountsTests(TestCase):
    def setUp(self):
        self.campus = Campus.objects.create(name="State University", email_domain="state.edu")
        self.verified_user = User.objects.create_user(
            username="verified_student",
            password="Password123!",
            college_email="alice@state.edu",
            is_email_verified=True,
            campus=self.campus,
        )
        self.unverified_user = User.objects.create_user(
            username="unverified_student",
            password="Password123!",
            college_email="bob@state.edu",
            is_email_verified=False,
            campus=self.campus,
        )

    def test_signup_rejects_email_outside_campus_domain(self):
        with self.settings(ALLOW_ANY_EMAIL_DOMAIN=False):
            response = self.client.post(
                reverse("accounts:signup"),
                {
                    "username": "outsider",
                    "college_email": "outsider@gmail.com",
                    "password": "Password123!",
                    "password_confirm": "Password123!",
                },
            )
            self.assertEqual(response.status_code, 200)
            self.assertFormError(
                response.context["form"],
                "college_email",
                "The email domain '@gmail.com' is not registered with any supported campus.",
            )
            self.assertFalse(User.objects.filter(username="outsider").exists())

    def test_signup_accepts_any_email_domain_when_allow_all_enabled(self):
        with self.settings(ALLOW_ANY_EMAIL_DOMAIN=True):
            response = self.client.post(
                reverse("accounts:signup"),
                {
                    "username": "mit_student",
                    "college_email": "student@mit.edu",
                    "password": "Password123!",
                    "password_confirm": "Password123!",
                },
            )
            self.assertEqual(response.status_code, 302)
            new_user = User.objects.get(username="mit_student")
            self.assertEqual(new_user.campus.email_domain, "mit.edu")

    def test_signup_accepts_valid_campus_domain_and_sends_email(self):
        mail.outbox.clear()
        response = self.client.post(
            reverse("accounts:signup"),
            {
                "username": "new_student",
                "college_email": "newbie@state.edu",
                "password": "Password123!",
                "password_confirm": "Password123!",
                "department": "Engineering",
                "year": "Freshman",
            },
        )
        self.assertEqual(response.status_code, 302)
        new_user = User.objects.get(username="new_student")
        self.assertTrue(new_user.is_email_verified)
        self.assertEqual(new_user.campus, self.campus)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("Verify your UniSwap Campus Account", mail.outbox[0].subject)

    def test_verification_token_flow(self):
        token = generate_verification_token(self.unverified_user)
        self.assertIsNotNone(token)

        response = self.client.get(reverse("accounts:verify", kwargs={"token": token}))
        self.assertEqual(response.status_code, 302)
        self.unverified_user.refresh_from_db()
        self.assertTrue(self.unverified_user.is_email_verified)

    def test_invalid_verification_token_rejected(self):
        response = self.client.get(reverse("accounts:verify", kwargs={"token": "invalid-token-123"}))
        self.assertEqual(response.status_code, 400)
        self.unverified_user.refresh_from_db()
        self.assertFalse(self.unverified_user.is_email_verified)

    def test_unverified_user_blocked_from_profile(self):
        self.client.login(username="unverified_student", password="Password123!")
        profile_url = reverse("user_profile", kwargs={"pk": self.verified_user.pk})
        response = self.client.get(profile_url)
        self.assertRedirects(response, reverse("accounts:verify_notice"))

    def test_verified_user_can_access_profile(self):
        self.client.login(username="verified_student", password="Password123!")
        profile_url = reverse("user_profile", kwargs={"pk": self.verified_user.pk})
        response = self.client.get(profile_url)
        self.assertEqual(response.status_code, 200)
