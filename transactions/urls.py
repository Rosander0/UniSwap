from django.urls import path
from . import views

app_name = "transactions"

urlpatterns = [
    path("", views.TransactionListView.as_view(), name="list"),
    path("request/<int:listing_id>/", views.RequestDealView.as_view(), name="request_deal"),
    path("<int:id>/agree/", views.AgreeDealView.as_view(), name="agree"),
    path("<int:id>/complete/", views.CompleteDealView.as_view(), name="complete"),
]
