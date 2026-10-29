from django.contrib import admin
from .models import Transaction


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ("listing", "buyer", "seller", "status", "completed_at", "created_at")
    list_filter = ("status", "created_at", "completed_at")
    search_fields = ("listing__title", "buyer__username", "seller__username")
