from django.urls import path
from . import views

app_name = "listings"

urlpatterns = [
    path("", views.ListingListView.as_view(), name="list"),
    path("new/", views.ListingCreateView.as_view(), name="create"),
    path("<int:id>/", views.ListingDetailView.as_view(), name="detail"),
    path("<int:id>/edit/", views.ListingUpdateView.as_view(), name="edit"),
    path("<int:id>/delete/", views.ListingDeleteView.as_view(), name="delete"),
]
