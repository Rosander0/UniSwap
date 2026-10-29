from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.http import HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View

from accounts.mixins import VerifiedRequiredMixin
from listings.models import Listing
from .models import Conversation, Message


class InboxView(VerifiedRequiredMixin, View):
    def get(self, request):
        conversations = (
            Conversation.objects.filter(Q(buyer=request.user) | Q(seller=request.user))
            .select_related("listing", "buyer", "seller")
            .prefetch_related("messages")
        )
        return render(request, "messaging/inbox.html", {"conversations": conversations})


class StartConversationView(VerifiedRequiredMixin, View):
    def get(self, request, listing_id):
        listing = get_object_or_404(Listing, pk=listing_id)
        if listing.seller_id == request.user.id:
            messages.error(request, "You cannot message about your own listing.")
            return redirect("listings:detail", id=listing.id)

        conversation, _ = Conversation.objects.get_or_create(
            listing=listing,
            buyer=request.user,
            defaults={"seller": listing.seller},
        )
        return redirect("messaging:detail", conv_id=conversation.id)


class ConversationDetailView(VerifiedRequiredMixin, View):
    def get(self, request, conv_id):
        # IDOR prevention: filter to current user as participant before get_object_or_404
        user_conversations = Conversation.objects.filter(
            Q(buyer=request.user) | Q(seller=request.user)
        ).select_related("listing", "buyer", "seller")
        conversation = get_object_or_404(user_conversations, pk=conv_id)

        chat_messages = conversation.messages.select_related("sender").all()
        other_party = (
            conversation.seller if request.user == conversation.buyer else conversation.buyer
        )
        return render(
            request,
            "messaging/conversation.html",
            {
                "conversation": conversation,
                "chat_messages": chat_messages,
                "other_party": other_party,
            },
        )

    def post(self, request, conv_id):
        user_conversations = Conversation.objects.filter(
            Q(buyer=request.user) | Q(seller=request.user)
        )
        conversation = get_object_or_404(user_conversations, pk=conv_id)

        body = request.POST.get("body", "").strip()
        if not body:
            return redirect("messaging:detail", conv_id=conversation.id)

        Message.objects.create(
            conversation=conversation,
            sender=request.user,
            body=body,
        )
        return redirect("messaging:detail", conv_id=conversation.id)
