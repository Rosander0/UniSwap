from decimal import Decimal
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from accounts.models import Campus
from listings.models import Category, Listing

User = get_user_model()


class Command(BaseCommand):
    help = "Seeds campus marketplace categories, sample campuses, and sample listings"

    def handle(self, *args, **options):
        # 1. Seed Categories
        categories_data = [
            ("Textbooks", "textbooks"),
            ("Calculators", "calculators"),
            ("Lab Coats", "lab-coats"),
            ("Electronics", "electronics"),
            ("Other", "other"),
        ]
        cats = {}
        for name, slug in categories_data:
            cat, created = Category.objects.get_or_create(slug=slug, defaults={"name": name})
            cats[slug] = cat
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created category: {name}"))

        # 2. Seed Campuses
        campuses = [
            ("State University", "state.edu"),
            ("MIT", "mit.edu"),
            ("Stanford University", "stanford.edu"),
            ("Harvard University", "harvard.edu"),
            ("General College", "gmail.com"),
        ]
        campus = None
        for name, domain in campuses:
            c, _ = Campus.objects.get_or_create(email_domain=domain, defaults={"name": name})
            if domain == "state.edu":
                campus = c
        self.stdout.write(self.style.SUCCESS("Configured campus domains."))

        # 3. Seed Sample Users
        seller, _ = User.objects.get_or_create(
            username="alice_senior",
            defaults={
                "college_email": "alice@state.edu",
                "campus": campus,
                "department": "Computer Science",
                "year": "Senior",
                "is_email_verified": True,
            },
        )
        if _:
            seller.set_password("StudentPass123!")
            seller.save()

        buyer, _ = User.objects.get_or_create(
            username="bob_sophomore",
            defaults={
                "college_email": "bob@state.edu",
                "campus": campus,
                "department": "Biology",
                "year": "Sophomore",
                "is_email_verified": True,
            },
        )
        if _:
            buyer.set_password("StudentPass123!")
            buyer.save()

        # 4. Seed Sample Listings
        sample_listings = [
            {
                "title": "TI-84 Plus CE Graphing Calculator (Rose Gold)",
                "category": cats["calculators"],
                "condition": "Like New",
                "price": Decimal("75.00"),
                "description": "Used for one semester of Calculus II. Battery holds charge for weeks, charger and slide case included.",
            },
            {
                "title": "Campbell Biology 12th Edition Hardcover",
                "category": cats["textbooks"],
                "condition": "Good",
                "price": Decimal("55.00"),
                "description": "Essential for BIO 101/102. Minimal highlighting in chapters 1-4, spine and pages are crisp.",
            },
            {
                "title": "Unisex 100% Cotton Lab Coat (Size M)",
                "category": cats["lab-coats"],
                "condition": "Like New",
                "price": Decimal("18.00"),
                "description": "Complies with Chemistry department safety requirements. Washed and pressed, no stains or tears.",
            },
            {
                "title": "Sony WH-1000XM4 Noise Canceling Headphones",
                "category": cats["electronics"],
                "condition": "Good",
                "price": Decimal("140.00"),
                "description": "Perfect for library study sessions. Works great, includes carrying case and aux cable.",
            },
            {
                "title": "Introduction to Algorithms (CLRS) 4th Edition",
                "category": cats["textbooks"],
                "condition": "New",
                "price": Decimal("65.00"),
                "description": "Brand new copy for CS 310. Never opened shrink wrap because I dropped the course.",
            },
        ]

        for item in sample_listings:
            listing, created = Listing.objects.get_or_create(
                title=item["title"],
                seller=seller,
                defaults={
                    "campus": campus,
                    "category": item["category"],
                    "condition": item["condition"],
                    "price": item["price"],
                    "description": item["description"],
                    "status": "Active",
                },
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created listing: {listing.title}"))

        self.stdout.write(self.style.SUCCESS("Database seeding completed successfully!"))

