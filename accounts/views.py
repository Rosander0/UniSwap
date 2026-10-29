from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model, login
from django.contrib.auth.views import LoginView, LogoutView
from django.core.mail import send_mail
from django.db.models import Avg, Count
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.views import View
from django.views.generic import CreateView, DetailView, TemplateView

from .forms import SignUpForm
from .mixins import VerifiedRequiredMixin
from .tokens import generate_verification_token, verify_token

User = get_user_model()


class SignUpView(CreateView):
    form_class = SignUpForm
    template_name = "accounts/signup.html"
    success_url = reverse_lazy("listings:list")

    def form_valid(self, form):
        user = form.save()
        if getattr(settings, "REQUIRE_EMAIL_VERIFICATION", False):
            token = generate_verification_token(user)
            verify_url = self.request.build_absolute_uri(
                reverse("accounts:verify", kwargs={"token": token})
            )
            send_mail(
                subject="Verify your UniSwap Campus Account",
                message=f"Please verify your college email: {verify_url}",
                from_email=None,
                recipient_list=[user.college_email],
                fail_silently=False,
            )
        # Direct login: verification is disabled / dummy
        login(self.request, user)
        messages.success(
            self.request,
            f"Account created successfully! Welcome to UniSwap, {user.username}.",
        )
        return redirect("listings:list")


class VerifyEmailView(View):
    def get(self, request, token):
        user = verify_token(token)
        if user:
            user.is_email_verified = True
            user.save(update_fields=["is_email_verified"])
            messages.success(
                request,
                f"Thank you, {user.username}! Your college email has been verified. You now have full access to UniSwap.",
            )
            return redirect("accounts:login")
        messages.error(
            request,
            "This verification link is invalid or has expired. Please sign up again or contact campus support.",
        )
        return render(request, "accounts/verify_failed.html", status=400)


class VerifyNoticeView(TemplateView):
    template_name = "accounts/verify_notice.html"


class ResendVerificationView(View):
    def post(self, request):
        if not request.user.is_authenticated:
            return redirect("accounts:login")
        if request.user.is_email_verified:
            messages.info(request, "Your email is already verified.")
            return redirect("listings:list")

        token = generate_verification_token(request.user)
        verify_url = request.build_absolute_uri(
            reverse("accounts:verify", kwargs={"token": token})
        )
        send_mail(
            subject="Verify your UniSwap Campus Account",
            message=f"Please verify your email: {verify_url}",
            from_email=None,
            recipient_list=[request.user.college_email],
            fail_silently=False,
        )
        messages.info(request, "A fresh verification link was sent to your email.")
        return redirect("accounts:verify_notice")


class ProfileDetailView(VerifiedRequiredMixin, DetailView):
    model = User
    template_name = "accounts/profile.html"
    context_object_name = "profile_user"
    pk_url_kwarg = "pk"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        profile_user = self.object

        # Calculate average rating using aggregate
        from reviews.models import Review
        from listings.models import Listing

        stats = Review.objects.filter(reviewee=profile_user).aggregate(
            avg_rating=Avg("rating"),
            total_reviews=Count("id"),
        )
        context["avg_rating"] = stats["avg_rating"]
        context["total_reviews"] = stats["total_reviews"]
        context["recent_reviews"] = (
            Review.objects.filter(reviewee=profile_user)
            .select_related("reviewer", "transaction__listing")
            .order_by("-created_at")[:10]
        )
        context["active_listings"] = Listing.objects.filter(
            seller=profile_user, status="Active"
        ).order_by("-created_at")
        return context
