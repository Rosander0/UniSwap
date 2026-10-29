from decimal import Decimal
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from accounts.models import Campus
from listings.models import Category, Listing
from messaging.models import Conversation, Message
from transactions.models import Transaction

User = get_user_model()


class IDORProtectionTests(TestCase):
    def setUp(self):
        self.campus = Campus.objects.create(name="Tech Institute", email_domain="tech.edu")
        self.seller = User.objects.create_user(
            username="seller_user",
            college_email="seller@tech.edu",
            password="Password123!",
            is_email_verified=True,
            campus=self.campus,
        )
        self.buyer = User.objects.create_user(
            username="buyer_user",
            college_email="buyer@tech.edu",
            password="Password123!",
            is_email_verified=True,
            campus=self.campus,
        )
        self.outsider = User.objects.create_user(
            username="outsider_user",
            college_email="outsider@tech.edu",
            password="Password123!",
            is_email_verified=True,
            campus=self.campus,
        )
        self.category, _ = Category.objects.get_or_create(slug="electronics", defaults={"name": "Electronics"})
        self.listing = Listing.objects.create(
            seller=self.seller,
            campus=self.campus,
            category=self.category,
            title="USB-C Hub",
            description="Multiport adapter",
            price=Decimal("25.00"),
            condition="Like New",
            status="Active",
        )
        self.conversation = Conversation.objects.create(
            listing=self.listing,
            buyer=self.buyer,
            seller=self.seller,
        )
        self.transaction = Transaction.objects.create(
            listing=self.listing,
            buyer=self.buyer,
            seller=self.seller,
            status="Completed",
        )

    def test_non_participant_gets_404_on_conversation_url(self):
        self.client.login(username="outsider_user", password="Password123!")
        conv_url = reverse("messaging:detail", kwargs={"conv_id": self.conversation.id})

        get_res = self.client.get(conv_url)
        self.assertEqual(get_res.status_code, 404)

        post_res = self.client.post(conv_url, {"body": "Sneaky message"})
        self.assertEqual(post_res.status_code, 404)

    def test_non_participant_gets_404_on_transaction_agree_url(self):
        self.client.login(username="outsider_user", password="Password123!")
        agree_url = reverse("transactions:agree", kwargs={"id": self.transaction.id})
        response = self.client.post(agree_url)
        self.assertEqual(response.status_code, 404)

    def test_non_participant_gets_404_on_transaction_complete_url(self):
        self.client.login(username="outsider_user", password="Password123!")
        complete_url = reverse("transactions:complete", kwargs={"id": self.transaction.id})
        response = self.client.post(complete_url)
        self.assertEqual(response.status_code, 404)

    def test_non_participant_gets_404_on_review_url(self):
        self.client.login(username="outsider_user", password="Password123!")
        review_url = reverse("reviews:create_review", kwargs={"id": self.transaction.id})

        get_res = self.client.get(review_url)
        self.assertEqual(get_res.status_code, 404)

        post_res = self.client.post(review_url, {"rating": 5, "comment": "Great deal"})
        self.assertEqual(post_res.status_code, 404)
