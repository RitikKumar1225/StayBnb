from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from bookings.models import Booking
from properties.models import Property
from .forms import ReviewForm
from .models import Review


@login_required
def create(request, property_id):
    listing = get_object_or_404(Property, pk=property_id)
    eligible = Booking.objects.filter(
        property=listing,
        guest=request.user,
        check_out__lte=timezone.localdate(),
        status=Booking.CONFIRMED,
    ).exists()
    if not eligible:
        messages.error(request, "Reviews are available after a completed stay.")
        return redirect(listing.get_absolute_url())
    if Review.objects.filter(property=listing, guest=request.user).exists():
        messages.info(request, "You’ve already reviewed this stay.")
        return redirect(listing.get_absolute_url())
    form = ReviewForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        review = form.save(commit=False)
        review.property = listing
        review.guest = request.user
        review.save()
        messages.success(request, "Thanks for sharing a little of your stay.")
        return redirect(listing.get_absolute_url())
    return render(request, "reviews/review_form.html", {"form": form, "property": listing})
