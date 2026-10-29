from django.contrib import messages
from django.db.models import Q
from django.http import HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View

from accounts.mixins import VerifiedRequiredMixin
from transactions.models import Transaction
from .forms import ReviewForm
from .models import Review


class CreateReviewView(VerifiedRequiredMixin, View):
    def get(self, request, id):
        # IDOR prevention: filter to current user as participant before get_object_or_404
        user_deals = Transaction.objects.filter(Q(buyer=request.user) | Q(seller=request.user)).select_related(
            "listing", "buyer", "seller"
        )
        deal = get_object_or_404(user_deals, pk=id)

        # Gate 1: Transaction must be Completed
        if deal.status != "Completed":
            return HttpResponseBadRequest("A review is allowed only on a Completed transaction.")

        # Gate 2: One review per transaction (second review rejected)
        if Review.objects.filter(transaction=deal).exists():
            return HttpResponseBadRequest("This transaction has already been reviewed.")

        reviewee = deal.seller if request.user == deal.buyer else deal.buyer
        form = ReviewForm()
        return render(
            request,
            "reviews/review_form.html",
            {"form": form, "deal": deal, "reviewee": reviewee},
        )

    def post(self, request, id):
        user_deals = Transaction.objects.filter(Q(buyer=request.user) | Q(seller=request.user))
        deal = get_object_or_404(user_deals, pk=id)

        # Gate 1: Completed status check
        if deal.status != "Completed":
            return HttpResponseBadRequest("A review is allowed only on a Completed transaction.")

        # Gate 2: Second review rejected
        if Review.objects.filter(transaction=deal).exists():
            return HttpResponseBadRequest("This transaction has already been reviewed.")

        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.transaction = deal
            review.reviewer = request.user
            review.reviewee = deal.seller if request.user == deal.buyer else deal.buyer
            review.save()

            messages.success(request, f"Review submitted for @{review.reviewee.username}! Thank you.")
            return redirect("user_profile", pk=review.reviewee.pk)

        reviewee = deal.seller if request.user == deal.buyer else deal.buyer
        return render(
            request,
            "reviews/review_form.html",
            {"form": form, "deal": deal, "reviewee": reviewee},
        )
