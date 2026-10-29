from django.contrib import messages
from django.db.models import Q
from django.http import HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views import View

from accounts.mixins import VerifiedRequiredMixin
from listings.models import Listing
from .models import Transaction


class TransactionListView(VerifiedRequiredMixin, View):
    def get(self, request):
        deals = (
            Transaction.objects.filter(Q(buyer=request.user) | Q(seller=request.user))
            .select_related("listing", "buyer", "seller")
            .order_by("-created_at")
        )
        return render(request, "transactions/deal_list.html", {"deals": deals})


class RequestDealView(VerifiedRequiredMixin, View):
    def post(self, request, listing_id):
        listing = get_object_or_404(Listing, pk=listing_id)
        if listing.seller_id == request.user.id:
            return HttpResponseBadRequest("You cannot purchase your own listing.")

        if listing.status not in ("Active", "Reserved"):
            return HttpResponseBadRequest(f"Cannot request a deal for a {listing.status.lower()} listing.")

        # Check if an active deal already exists between this buyer and listing
        deal = Transaction.objects.filter(
            listing=listing,
            buyer=request.user,
            status__in=["Requested", "Agreed"],
        ).first()

        if not deal:
            deal = Transaction.objects.create(
                listing=listing,
                buyer=request.user,
                seller=listing.seller,
                status="Requested",
            )
            messages.success(request, f"Deal requested for '{listing.title}'! Waiting for seller agreement.")
        else:
            messages.info(request, f"You already have an open deal for '{listing.title}'.")

        return redirect("transactions:list")


class AgreeDealView(VerifiedRequiredMixin, View):
    def post(self, request, id):
        # IDOR prevention: filter to current user as participant before get_object_or_404
        user_deals = Transaction.objects.filter(Q(buyer=request.user) | Q(seller=request.user))
        deal = get_object_or_404(user_deals, pk=id)

        # State transition: Requested -> Agreed (seller only)
        if deal.status != "Requested":
            return HttpResponseBadRequest(
                f"Invalid transition: Cannot agree to a deal with status '{deal.status}'."
            )

        if deal.seller_id != request.user.id:
            return HttpResponseBadRequest("Invalid transition: Only the seller can agree to a deal request.")

        deal.status = "Agreed"
        deal.save(update_fields=["status"])

        deal.listing.status = "Reserved"
        deal.listing.save(update_fields=["status"])

        messages.success(request, f"Deal agreed! Please coordinate campus meetup with @{deal.buyer.username}.")
        return redirect("transactions:list")


class CompleteDealView(VerifiedRequiredMixin, View):
    def post(self, request, id):
        # IDOR prevention: filter to current user as participant before get_object_or_404
        user_deals = Transaction.objects.filter(Q(buyer=request.user) | Q(seller=request.user))
        deal = get_object_or_404(user_deals, pk=id)

        # State transition: Agreed -> Completed (buyer or seller)
        if deal.status != "Agreed":
            return HttpResponseBadRequest(
                f"Invalid transition: Cannot complete a deal with status '{deal.status}'. Deal must be 'Agreed' first."
            )

        if request.user.id not in (deal.buyer_id, deal.seller_id):
            return HttpResponseBadRequest("Invalid transition: Only a participant can mark the deal completed.")

        deal.status = "Completed"
        deal.completed_at = timezone.now()
        deal.save(update_fields=["status", "completed_at"])

        # Completing sets the listing to Sold
        deal.listing.status = "Sold"
        deal.listing.save(update_fields=["status"])

        messages.success(request, f"Deal completed! Listing '{deal.listing.title}' is marked as Sold.")
        return redirect("transactions:list")
