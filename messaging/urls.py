from django.urls import path
from . import views

app_name = "messaging"

urlpatterns = [
    path("", views.InboxView.as_view(), name="inbox"),
    path("start/<int:listing_id>/", views.StartConversationView.as_view(), name="start_conversation"),
    path("<int:conv_id>/", views.ConversationDetailView.as_view(), name="detail"),
]
