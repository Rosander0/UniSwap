from decimal import Decimal
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from accounts.models import Campus
from listings.models import Category, Listing

User = get_user_model()


class ListingOwnershipTests(TestCase):
    def setUp(self):
        self.campus = Campus.objects.create(name="Tech Institute", email_domain="tech.edu")
        self.owner = User.objects.create_user(
            username="owner_user",
            college_email="owner@tech.edu",
            password="Password123!",
            is_email_verified=True,
            campus=self.campus,
        )
        self.non_owner = User.objects.create_user(
            username="other_user",
            college_email="other@tech.edu",
            password="Password123!",
            is_email_verified=True,
            campus=self.campus,
        )
        self.category, _ = Category.objects.get_or_create(slug="calculators", defaults={"name": "Calculators"})
        self.listing = Listing.objects.create(
            seller=self.owner,
            campus=self.campus,
            category=self.category,
            title="TI-84 Plus",
            description="Working perfectly",
            price=Decimal("60.00"),
            condition="Good",
            status="Active",
        )

    def test_owner_can_get_and_post_edit(self):
        self.client.login(username="owner_user", password="Password123!")
        edit_url = reverse("listings:edit", kwargs={"id": self.listing.id})
        get_res = self.client.get(edit_url)
        self.assertEqual(get_res.status_code, 200)

        post_res = self.client.post(
            edit_url,
            {
                "title": "TI-84 Plus Silver Edition",
                "category": self.category.id,
                "price": "65.00",
                "condition": "Like New",
                "description": "Updated description",
                "images-TOTAL_FORMS": "0",
                "images-INITIAL_FORMS": "0",
            },
        )
        self.assertEqual(post_res.status_code, 302)
        self.listing.refresh_from_db()
        self.assertEqual(self.listing.title, "TI-84 Plus Silver Edition")
        self.assertEqual(self.listing.price, Decimal("65.00"))

    def test_non_owner_forbidden_from_editing_listing(self):
        self.client.login(username="other_user", password="Password123!")
        edit_url = reverse("listings:edit", kwargs={"id": self.listing.id})

        get_res = self.client.get(edit_url)
        self.assertEqual(get_res.status_code, 403)

        post_res = self.client.post(
            edit_url,
            {
                "title": "Hacked Title",
                "category": self.category.id,
                "price": "1.00",
                "condition": "Fair",
                "description": "Unauthorized edit",
                "images-TOTAL_FORMS": "0",
                "images-INITIAL_FORMS": "0",
            },
        )
        self.assertEqual(post_res.status_code, 403)
        self.listing.refresh_from_db()
        self.assertEqual(self.listing.title, "TI-84 Plus")

    def test_non_owner_forbidden_from_deleting_listing(self):
        self.client.login(username="other_user", password="Password123!")
        delete_url = reverse("listings:delete", kwargs={"id": self.listing.id})

        get_res = self.client.get(delete_url)
        self.assertEqual(get_res.status_code, 403)

        post_res = self.client.post(delete_url)
        self.assertEqual(post_res.status_code, 403)
        self.listing.refresh_from_db()
        self.assertEqual(self.listing.status, "Active")

    def test_owner_deletion_marks_status_removed_rather_than_deleting_row(self):
        self.client.login(username="owner_user", password="Password123!")
        delete_url = reverse("listings:delete", kwargs={"id": self.listing.id})
        response = self.client.post(delete_url)
        self.assertEqual(response.status_code, 302)

        # Confirm the row still exists in DB but with status 'Removed'
        listing_id = self.listing.id
        self.assertTrue(Listing.objects.filter(pk=listing_id).exists())
        self.listing.refresh_from_db()
        self.assertEqual(self.listing.status, "Removed")
