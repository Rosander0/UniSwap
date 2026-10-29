from decimal import Decimal
from django.contrib.auth import get_user_model
from django.db.models import Avg
from django.test import TestCase
from django.urls import reverse
from accounts.models import Campus
from listings.models import Category, Listing
from reviews.models import Review
from transactions.models import Transaction

User = get_user_model()


class ReviewGateAndRatingTests(TestCase):
    def setUp(self):
        self.campus = Campus.objects.create(name="Metro College", email_domain="metro.edu")
        self.seller = User.objects.create_user(
            username="seller_sara",
            college_email="sara@metro.edu",
            password="Password123!",
            is_email_verified=True,
            campus=self.campus,
        )
        self.buyer = User.objects.create_user(
            username="buyer_bill",
            college_email="bill@metro.edu",
            password="Password123!",
            is_email_verified=True,
            campus=self.campus,
        )
        self.outsider = User.objects.create_user(
            username="outsider_dan",
            college_email="dan@metro.edu",
            password="Password123!",
            is_email_verified=True,
            campus=self.campus,
        )
        self.category, _ = Category.objects.get_or_create(slug="textbooks", defaults={"name": "Textbooks"})
        self.listing = Listing.objects.create(
            seller=self.seller,
            campus=self.campus,
            category=self.category,
            title="Linear Algebra 5th Edition",
            description="Hardcover textbook",
            price=Decimal("45.00"),
            condition="Good",
            status="Sold",
        )
        self.deal = Transaction.objects.create(
            listing=self.listing,
            buyer=self.buyer,
            seller=self.seller,
            status="Completed",
        )

    def test_review_rejected_before_deal_completion(self):
        uncompleted_deal = Transaction.objects.create(
            listing=self.listing,
            buyer=self.buyer,
            seller=self.seller,
            status="Agreed",
        )
        self.client.login(username="buyer_bill", password="Password123!")
        url = reverse("reviews:create_review", kwargs={"id": uncompleted_deal.id})

        res_get = self.client.get(url)
        self.assertEqual(res_get.status_code, 400)

        res_post = self.client.post(url, {"rating": 5, "comment": "Premature review"})
        self.assertEqual(res_post.status_code, 400)
        self.assertFalse(Review.objects.filter(transaction=uncompleted_deal).exists())

    def test_review_rejected_for_non_parties(self):
        self.client.login(username="outsider_dan", password="Password123!")
        url = reverse("reviews:create_review", kwargs={"id": self.deal.id})

        res_get = self.client.get(url)
        self.assertEqual(res_get.status_code, 404)

        res_post = self.client.post(url, {"rating": 5, "comment": "Intruder review"})
        self.assertEqual(res_post.status_code, 404)

    def test_buyer_can_review_completed_deal_and_seller_is_reviewee(self):
        self.client.login(username="buyer_bill", password="Password123!")
        url = reverse("reviews:create_review", kwargs={"id": self.deal.id})

        res_post = self.client.post(url, {"rating": 5, "comment": "Smooth campus meetup!"})
        self.assertEqual(res_post.status_code, 302)

        review = Review.objects.get(transaction=self.deal)
        self.assertEqual(review.reviewer, self.buyer)
        self.assertEqual(review.reviewee, self.seller)
        self.assertEqual(review.rating, 5)

    def test_second_review_on_same_transaction_is_rejected(self):
        # First review created
        Review.objects.create(
            transaction=self.deal,
            reviewer=self.buyer,
            reviewee=self.seller,
            rating=5,
            comment="First review",
        )

        # Attempt second review
        self.client.login(username="buyer_bill", password="Password123!")
        url = reverse("reviews:create_review", kwargs={"id": self.deal.id})

        res_get = self.client.get(url)
        self.assertEqual(res_get.status_code, 400)

        res_post = self.client.post(url, {"rating": 4, "comment": "Second review attempt"})
        self.assertEqual(res_post.status_code, 400)
        self.assertEqual(Review.objects.filter(transaction=self.deal).count(), 1)

    def test_rating_average_updates_correctly_on_profile(self):
        # Deal 1: 5 stars
        Review.objects.create(
            transaction=self.deal,
            reviewer=self.buyer,
            reviewee=self.seller,
            rating=5,
            comment="Awesome seller!",
        )

        # Deal 2 with another buyer: 3 stars
        buyer2 = User.objects.create_user(
            username="buyer_charlie",
            college_email="charlie@metro.edu",
            password="Password123!",
            is_email_verified=True,
            campus=self.campus,
        )
        cat2, _ = Category.objects.get_or_create(slug="calculators", defaults={"name": "Calculators"})
        listing2 = Listing.objects.create(
            seller=self.seller,
            campus=self.campus,
            category=cat2,
            title="Calculator TI-30",
            description="Basic scientific calculator",
            price=Decimal("15.00"),
            condition="Good",
            status="Sold",
        )
        deal2 = Transaction.objects.create(
            listing=listing2,
            buyer=buyer2,
            seller=self.seller,
            status="Completed",
        )
        Review.objects.create(
            transaction=deal2,
            reviewer=buyer2,
            reviewee=self.seller,
            rating=3,
            comment="Item had some scratches but works.",
        )

        # Aggregate average should be (5 + 3) / 2 = 4.0
        avg = Review.objects.filter(reviewee=self.seller).aggregate(Avg("rating"))["rating__avg"]
        self.assertEqual(avg, 4.0)

        # View seller profile and check calculated avg in context
        self.client.login(username="buyer_bill", password="Password123!")
        profile_url = reverse("user_profile", kwargs={"pk": self.seller.pk})
        response = self.client.get(profile_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["avg_rating"], 4.0)
        self.assertEqual(response.context["total_reviews"], 2)
