from django.contrib.auth.views import LoginView, LogoutView
from django.urls import path
from . import views

app_name = "accounts"

urlpatterns = [
    path("signup/", views.SignUpView.as_view(), name="signup"),
    path("verify/<str:token>/", views.VerifyEmailView.as_view(), name="verify"),
    path("verify-notice/", views.VerifyNoticeView.as_view(), name="verify_notice"),
    path("resend-verification/", views.ResendVerificationView.as_view(), name="resend_verification"),
    path("login/", LoginView.as_view(template_name="accounts/login.html"), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
]

