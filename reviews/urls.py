from django.urls import path
from . import views

app_name = "reviews"

urlpatterns = [
    path("deal/<int:id>/", views.CreateReviewView.as_view(), name="create_review"),
]
