from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.views.decorators.http import require_POST
from django.shortcuts import get_object_or_404, redirect, render

from properties.models import Property
from .forms import BookingForm
from .models import Booking
from .services import create_booking


@login_required
def create(request, property_id):
    listing = get_object_or_404(Property, pk=property_id)
    form = BookingForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        booking = create_booking(listing=listing, guest=request.user, form=form)
        if booking:
            messages.success(request, "Your booking request has been sent.")
            return redirect("users:dashboard")
    return render(request, "bookings/booking_form.html", {"form": form, "property": listing})


@login_required
@require_POST
def cancel(request, pk):
    booking = get_object_or_404(Booking, pk=pk)
    if request.user.id not in (booking.guest_id, booking.property.host_id):
        raise PermissionDenied
    if booking.status != Booking.CANCELLED:
        booking.status = Booking.CANCELLED
        booking.save(update_fields=["status"])
        messages.success(request, "The booking has been cancelled.")
    return redirect("users:dashboard")


@login_required
@require_POST
def update_status(request, pk):
    booking = get_object_or_404(Booking, pk=pk, property__host=request.user)
    status = request.POST.get("status")
    if booking.status != Booking.CANCELLED and status in (Booking.CONFIRMED, Booking.CANCELLED):
        booking.status = status
        booking.save(update_fields=["status"])
        messages.success(request, f"Booking {status}.")
    return redirect("users:dashboard")
