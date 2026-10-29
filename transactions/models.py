from django.conf import settings
from django.db import models


class Transaction(models.Model):
    STATUS_CHOICES = [
        ("Requested", "Requested"),
        ("Agreed", "Agreed"),
        ("Completed", "Completed"),
        ("Cancelled", "Cancelled"),
    ]

    listing = models.ForeignKey(
        "listings.Listing",
        on_delete=models.CASCADE,
        related_name="transactions",
    )
    buyer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="buyer_transactions",
    )
    seller = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="seller_transactions",
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="Requested")
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Deal for '{self.listing.title}': {self.status} (Buyer: {self.buyer.username}, Seller: {self.seller.username})"
