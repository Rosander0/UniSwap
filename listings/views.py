from decimal import Decimal, InvalidOperation
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.views import View
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from accounts.mixins import VerifiedRequiredMixin
from .forms import ListingForm, ListingImageFormSet
from .models import Category, Listing


class ListingListView(VerifiedRequiredMixin, ListView):
    model = Listing
    template_name = "listings/listing_list.html"
    context_object_name = "listings"
    paginate_by = 24

    def get_queryset(self):
        user = self.request.user
        qs = Listing.objects.filter(status="Active")

        # Campus scoped: students see listings for their campus
        if user.campus:
            qs = qs.filter(campus=user.campus)

        q = self.request.GET.get("q", "").strip()
        category_slug = self.request.GET.get("category", "").strip()
        condition = self.request.GET.get("condition", "").strip()
        min_price = self.request.GET.get("min", "").strip()
        max_price = self.request.GET.get("max", "").strip()

        if q:
            qs = qs.filter(Q(title__icontains=q) | Q(description__icontains=q))
        if category_slug:
            qs = qs.filter(category__slug=category_slug)
        if condition:
            qs = qs.filter(condition=condition)
        if min_price:
            try:
                qs = qs.filter(price__gte=Decimal(min_price))
            except InvalidOperation:
                pass
        if max_price:
            try:
                qs = qs.filter(price__lte=Decimal(max_price))
            except InvalidOperation:
                pass

        return qs.select_related("seller", "campus", "category").prefetch_related("images")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["categories"] = Category.objects.all()
        context["conditions"] = [c[0] for c in Listing.CONDITION_CHOICES]
        context["selected_q"] = self.request.GET.get("q", "")
        context["selected_category"] = self.request.GET.get("category", "")
        context["selected_condition"] = self.request.GET.get("condition", "")
        context["selected_min"] = self.request.GET.get("min", "")
        context["selected_max"] = self.request.GET.get("max", "")
        return context


class ListingDetailView(VerifiedRequiredMixin, DetailView):
    model = Listing
    template_name = "listings/listing_detail.html"
    context_object_name = "listing"
    pk_url_kwarg = "id"

    def get_queryset(self):
        # Exclude Removed listings unless owner is viewing
        return Listing.objects.select_related("seller", "campus", "category").prefetch_related("images")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        listing = self.object
        context["is_owner"] = listing.seller_id == self.request.user.id
        return context


class ListingCreateView(VerifiedRequiredMixin, View):
    def get(self, request):
        form = ListingForm()
        formset = ListingImageFormSet()
        return render(request, "listings/listing_form.html", {"form": form, "formset": formset, "action": "New"})

    def post(self, request):
        form = ListingForm(request.POST)
        formset = ListingImageFormSet(request.POST, request.FILES)

        if form.is_valid() and formset.is_valid():
            listing = form.save(commit=False)
            listing.seller = request.user
            listing.campus = request.user.campus
            listing.status = "Active"
            listing.save()

            formset.instance = listing
            formset.save()

            messages.success(request, f"Listing '{listing.title}' created successfully!")
            return redirect("listings:detail", id=listing.id)

        return render(request, "listings/listing_form.html", {"form": form, "formset": formset, "action": "New"})


class ListingUpdateView(VerifiedRequiredMixin, View):
    def get(self, request, id):
        listing = get_object_or_404(Listing, pk=id)
        if listing.seller != request.user:
            raise PermissionDenied("You do not have permission to edit this listing.")

        form = ListingForm(instance=listing)
        formset = ListingImageFormSet(instance=listing)
        return render(request, "listings/listing_form.html", {"form": form, "formset": formset, "action": "Edit", "listing": listing})

    def post(self, request, id):
        listing = get_object_or_404(Listing, pk=id)
        if listing.seller != request.user:
            raise PermissionDenied("You do not have permission to edit this listing.")

        form = ListingForm(request.POST, instance=listing)
        formset = ListingImageFormSet(request.POST, request.FILES, instance=listing)

        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            messages.success(request, "Listing updated successfully.")
            return redirect("listings:detail", id=listing.id)

        return render(request, "listings/listing_form.html", {"form": form, "formset": formset, "action": "Edit", "listing": listing})


class ListingDeleteView(VerifiedRequiredMixin, View):
    def get(self, request, id):
        listing = get_object_or_404(Listing, pk=id)
        if listing.seller != request.user:
            raise PermissionDenied("You do not have permission to delete this listing.")
        return render(request, "listings/listing_confirm_delete.html", {"listing": listing})

    def post(self, request, id):
        listing = get_object_or_404(Listing, pk=id)
        if listing.seller != request.user:
            raise PermissionDenied("You do not have permission to delete this listing.")

        # Deleting sets status to Removed rather than deleting the row
        listing.status = "Removed"
        listing.save(update_fields=["status"])
        messages.success(request, f"Listing '{listing.title}' has been removed.")
        return redirect("listings:list")
