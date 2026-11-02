from decimal import Decimal

from django.db import transaction

from .models import Booking


@transaction.atomic
def create_booking(*, listing, guest, form):
    dates = form.cleaned_data
    overlaps = Booking.objects.filter(property=listing).exclude(
        status=Booking.CANCELLED,
    ).filter(
        check_in__lt=dates["check_out"],
        check_out__gt=dates["check_in"],
    ).exists()
    if overlaps:
        form.add_error(None, "Those dates are no longer available. Try another stay.")
        return None
    if listing.host_id == guest.id:
        form.add_error(None, "You can’t book your own place.")
        return None

    nights = (dates["check_out"] - dates["check_in"]).days
    return Booking.objects.create(
        property=listing,
        guest=guest,
        check_in=dates["check_in"],
        check_out=dates["check_out"],
        guests=dates["guests"],
        total_price=listing.price_per_night * Decimal(nights),
    )
