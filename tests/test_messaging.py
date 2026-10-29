from decimal import Decimal
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from accounts.models import Campus
from listings.models import Category, Listing
from messaging.models import Conversation, Message

User = get_user_model()


class MessagingWorkflowTests(TestCase):
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
        self.category, _ = Category.objects.get_or_create(slug="electronics", defaults={"name": "Electronics"})
        self.listing = Listing.objects.create(
            seller=self.seller,
            campus=self.campus,
            category=self.category,
            title="Noise Canceling Headphones",
            description="Like new condition",
            price=Decimal("120.00"),
            condition="Like New",
            status="Active",
        )

    def test_user_cannot_message_their_own_listing(self):
        self.client.login(username="seller_user", password="Password123!")
        url = reverse("messaging:start_conversation", kwargs={"listing_id": self.listing.id})
        response = self.client.get(url)
        # Should redirect back to listing detail with an error message
        self.assertRedirects(response, reverse("listings:detail", kwargs={"id": self.listing.id}))
        self.assertEqual(Conversation.objects.count(), 0)

    def test_buyer_can_start_conversation_and_send_messages(self):
        self.client.login(username="buyer_user", password="Password123!")
        start_url = reverse("messaging:start_conversation", kwargs={"listing_id": self.listing.id})
        response = self.client.get(start_url)
        self.assertEqual(response.status_code, 302)

        conv = Conversation.objects.get(listing=self.listing, buyer=self.buyer)
        self.assertRedirects(response, reverse("messaging:detail", kwargs={"conv_id": conv.id}))

        # Post a message
        msg_url = reverse("messaging:detail", kwargs={"conv_id": conv.id})
        post_res = self.client.post(msg_url, {"body": "Hi, is this still available?"})
        self.assertRedirects(post_res, msg_url)

        self.assertEqual(conv.messages.count(), 1)
        msg = conv.messages.first()
        self.assertEqual(msg.sender, self.buyer)
        self.assertEqual(msg.body, "Hi, is this still available?")
