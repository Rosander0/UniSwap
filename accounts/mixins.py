from functools import wraps
from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.urls import reverse


class VerifiedRequiredMixin(LoginRequiredMixin):
    """
    Mixin ensuring user is authenticated. Email verification can be required
    via REQUIRE_EMAIL_VERIFICATION setting (defaults to False).
    """
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if getattr(settings, "REQUIRE_EMAIL_VERIFICATION", False) and not request.user.is_email_verified:
            return redirect("accounts:verify_notice")
        return super().dispatch(request, *args, **kwargs)


def verified_required(view_func):
    """Decorator for function-based views to enforce authentication."""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(f"{reverse('accounts:login')}?next={request.path}")
        if getattr(settings, "REQUIRE_EMAIL_VERIFICATION", False) and not request.user.is_email_verified:
            return redirect("accounts:verify_notice")
        return view_func(request, *args, **kwargs)
    return _wrapped_view

