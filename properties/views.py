from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied
from django.db.models import Avg
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from bookings.forms import BookingForm
from bookings.models import Booking
from bookings.services import create_booking
from reviews.forms import ReviewForm
from reviews.models import Review
from .forms import PropertyForm, PropertyImageUploadForm, PropertySearchForm
from .models import Property, PropertyImage


def home(request):
    listings = Property.objects.select_related("host").prefetch_related("images").annotate(rating=Avg("reviews__rating"))
    search_form = PropertySearchForm(request.GET or None)
    filters = {
        "location": request.GET.get("location", ""),
        "type": request.GET.get("type", ""),
        "min_price": request.GET.get("min_price", ""),
        "max_price": request.GET.get("max_price", ""),
    }
    if search_form.is_valid():
        cleaned = search_form.cleaned_data
        if cleaned["location"]:
            listings = listings.filter(location__icontains=cleaned["location"].strip())
        if cleaned["type"]:
            listings = listings.filter(property_type=cleaned["type"])
        if cleaned["min_price"] is not None:
            listings = listings.filter(price_per_night__gte=cleaned["min_price"])
        if cleaned["max_price"] is not None:
            listings = listings.filter(price_per_night__lte=cleaned["max_price"])
    return render(request, "properties/home.html", {
        "listings": listings,
        "types": Property.TYPE_CHOICES,
        "filters": filters,
        "search_form": search_form,
    })


def detail(request, pk):
    listing = get_object_or_404(
        Property.objects.select_related("host", "host__profile")
        .prefetch_related("images", "reviews__guest")
        .annotate(average_rating=Avg("reviews__rating")),
        pk=pk,
    )
    booking_form = BookingForm()
    review_form = ReviewForm()
    if request.user.is_authenticated:
        has_completed_stay = Booking.objects.filter(
            property=listing,
            guest=request.user,
            check_out__lte=timezone.localdate(),
            status=Booking.CONFIRMED,
        ).exists()
        has_reviewed = Review.objects.filter(property=listing, guest=request.user).exists()
    else:
        has_completed_stay = False
        has_reviewed = False
    can_review = has_completed_stay and not has_reviewed

    if request.method == "POST":
        action = request.POST.get("action")
        if action in ("book", "review") and not request.user.is_authenticated:
            return redirect_to_login(request.get_full_path(), reverse("users:login"))

        if action == "book":
            booking_form = BookingForm(request.POST)
            if booking_form.is_valid():
                booking = create_booking(listing=listing, guest=request.user, form=booking_form)
                if booking:
                    messages.success(request, "Your booking request has been sent.")
                    return redirect(listing.get_absolute_url())
        elif action == "review":
            if not has_completed_stay:
                messages.error(request, "You can review this place after a completed, confirmed stay.")
                return redirect(listing.get_absolute_url())
            if has_reviewed:
                messages.info(request, "You’ve already reviewed this stay.")
                return redirect(listing.get_absolute_url())
            review_form = ReviewForm(request.POST)
            if review_form.is_valid():
                review = review_form.save(commit=False)
                review.property = listing
                review.guest = request.user
                review.save()
                messages.success(request, "Thanks for sharing a little of your stay.")
                return redirect(listing.get_absolute_url())

    availability = list(
        listing.bookings.exclude(status=Booking.CANCELLED)
        .filter(check_out__gte=timezone.localdate())
        .order_by("check_in")
        .values("check_in", "check_out")
    )
    return render(request, "properties/detail.html", {
        "property": listing,
        "booking_form": booking_form,
        "review_form": review_form,
        "can_review": can_review,
        "has_completed_stay": has_completed_stay,
        "has_reviewed": has_reviewed,
        "availability": [
            {"check_in": stay["check_in"].isoformat(), "check_out": stay["check_out"].isoformat()}
            for stay in availability
        ],
        "today": timezone.localdate().isoformat(),
    })


@login_required
def create(request):
    form = PropertyForm(request.POST or None, request.FILES or None)
    image_form = PropertyImageUploadForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid() and image_form.is_valid():
        listing = form.save(commit=False)
        listing.host = request.user
        listing.save()
        for image in image_form.cleaned_data["images"]:
            PropertyImage.objects.create(property=listing, image=image)
        messages.success(request, "Your place is live.")
        return redirect(listing.get_absolute_url())
    return render(request, "properties/property_form.html", {"form": form, "image_form": image_form, "heading": "Make room for a good story"})


@login_required
def edit(request, pk):
    listing = get_object_or_404(Property, pk=pk)
    if listing.host_id != request.user.id:
        raise PermissionDenied
    old_cover_name = listing.cover_image.name
    form = PropertyForm(request.POST or None, request.FILES or None, instance=listing)
    image_form = PropertyImageUploadForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid() and image_form.is_valid():
        form.save()
        if old_cover_name and old_cover_name != listing.cover_image.name:
            listing.cover_image.storage.delete(old_cover_name)
        if "delete_cover_photo" in request.POST:
            if not request.FILES.get("cover_image") and listing.cover_image:
                listing.cover_image.delete(save=False)
            listing.cover_image_url = ""
            listing.save(update_fields=["cover_image", "cover_image_url"])
        for image in listing.images.filter(pk__in=request.POST.getlist("delete_images")):
            image.delete()
        for image in image_form.cleaned_data["images"]:
            PropertyImage.objects.create(property=listing, image=image)
        messages.success(request, "Your listing has been updated.")
        return redirect(listing.get_absolute_url())
    return render(request, "properties/property_form.html", {"form": form, "image_form": image_form, "property": listing, "heading": "A little refresh"})


@login_required
def delete(request, pk):
    listing = get_object_or_404(Property, pk=pk)
    if listing.host_id != request.user.id:
        raise PermissionDenied
    if request.method == "POST":
        listing.delete()
        messages.success(request, "Your listing has been removed.")
        return redirect("users:dashboard")
    return render(request, "properties/property_confirm_delete.html", {"property": listing})
