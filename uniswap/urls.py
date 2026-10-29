from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.shortcuts import redirect
from django.urls import include, path

from accounts.views import ProfileDetailView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", lambda request: redirect("listings:list"), name="home"),
    path("accounts/", include("accounts.urls", namespace="accounts")),
    path("listings/", include("listings.urls", namespace="listings")),
    path("messages/", include("messaging.urls", namespace="messaging")),
    path("deals/", include("transactions.urls", namespace="transactions")),
    path("reviews/", include("reviews.urls", namespace="reviews")),
    path("users/<int:pk>/", ProfileDetailView.as_view(), name="user_profile"),
]

# Ensure static and media files are always served in local development
urlpatterns += staticfiles_urlpatterns()
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
