from decimal import Decimal
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from accounts.models import Campus
from listings.models import Category, Listing
from transactions.models import Transaction

User = get_user_model()


class TransactionStateMachineTests(TestCase):
    def setUp(self):
        self.campus = Campus.objects.create(name="State College", email_domain="state.edu")
        self.seller = User.objects.create_user(
            username="seller_sam",
            college_email="seller@state.edu",
            password="Password123!",
            is_email_verified=True,
            campus=self.campus,
        )
        self.buyer = User.objects.create_user(
            username="buyer_ben",
            college_email="buyer@state.edu",
            password="Password123!",
            is_email_verified=True,
            campus=self.campus,
        )
        self.category, _ = Category.objects.get_or_create(slug="lab-coats", defaults={"name": "Lab Coats"})
        self.listing = Listing.objects.create(
            seller=self.seller,
            campus=self.campus,
            category=self.category,
            title="White Lab Coat",
            description="Size L",
            price=Decimal("20.00"),
            condition="Like New",
            status="Active",
        )

    def test_seller_cannot_request_deal_on_own_listing(self):
        self.client.login(username="seller_sam", password="Password123!")
        req_url = reverse("transactions:request_deal", kwargs={"listing_id": self.listing.id})
        response = self.client.post(req_url)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(Transaction.objects.count(), 0)

    def test_valid_full_lifecycle_requested_to_agreed_to_completed(self):
        # 1. Buyer requests deal
        self.client.login(username="buyer_ben", password="Password123!")
        req_url = reverse("transactions:request_deal", kwargs={"listing_id": self.listing.id})
        res = self.client.post(req_url)
        self.assertEqual(res.status_code, 302)

        deal = Transaction.objects.get(listing=self.listing, buyer=self.buyer)
        self.assertEqual(deal.status, "Requested")

        # 2. Seller agrees to deal
        self.client.login(username="seller_sam", password="Password123!")
        agree_url = reverse("transactions:agree", kwargs={"id": deal.id})
        agree_res = self.client.post(agree_url)
        self.assertEqual(agree_res.status_code, 302)

        deal.refresh_from_db()
        self.listing.refresh_from_db()
        self.assertEqual(deal.status, "Agreed")
        self.assertEqual(self.listing.status, "Reserved")

        # 3. Buyer marks deal completed
        self.client.login(username="buyer_ben", password="Password123!")
        comp_url = reverse("transactions:complete", kwargs={"id": deal.id})
        comp_res = self.client.post(comp_url)
        self.assertEqual(comp_res.status_code, 302)

        deal.refresh_from_db()
        self.listing.refresh_from_db()
        self.assertEqual(deal.status, "Completed")
        self.assertIsNotNone(deal.completed_at)
        self.assertEqual(self.listing.status, "Sold")

    def test_buyer_cannot_agree_to_deal(self):
        deal = Transaction.objects.create(
            listing=self.listing,
            buyer=self.buyer,
            seller=self.seller,
            status="Requested",
        )
        self.client.login(username="buyer_ben", password="Password123!")
        agree_url = reverse("transactions:agree", kwargs={"id": deal.id})
        res = self.client.post(agree_url)
        self.assertEqual(res.status_code, 400)

        deal.refresh_from_db()
        self.assertEqual(deal.status, "Requested")

    def test_cannot_complete_unagreed_deal(self):
        deal = Transaction.objects.create(
            listing=self.listing,
            buyer=self.buyer,
            seller=self.seller,
            status="Requested",
        )
        self.client.login(username="seller_sam", password="Password123!")
        comp_url = reverse("transactions:complete", kwargs={"id": deal.id})
        res = self.client.post(comp_url)
        self.assertEqual(res.status_code, 400)

        deal.refresh_from_db()
        self.assertEqual(deal.status, "Requested")

    def test_cannot_agree_to_completed_or_already_agreed_deal(self):
        deal = Transaction.objects.create(
            listing=self.listing,
            buyer=self.buyer,
            seller=self.seller,
            status="Agreed",
        )
        self.client.login(username="seller_sam", password="Password123!")
        agree_url = reverse("transactions:agree", kwargs={"id": deal.id})
        res = self.client.post(agree_url)
        self.assertEqual(res.status_code, 400)
