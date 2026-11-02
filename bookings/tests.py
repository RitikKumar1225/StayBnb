from datetime import timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from properties.models import Property
from .models import Booking


class BookingFlowTests(TestCase):
    def setUp(self):
        self.host = User.objects.create_user(username="host", password="test-password-123")
        self.guest = User.objects.create_user(username="guest", password="test-password-123")
        self.property = Property.objects.create(
            host=self.host,
            title="The Long Weekend",
            description="Room to breathe.",
            location="Goa",
            price_per_night=Decimal("3200.00"),
        )
        self.check_in = timezone.localdate() + timedelta(days=20)
        self.check_out = self.check_in + timedelta(days=3)

    def test_booking_totals_and_blocks_overlapping_dates(self):
        self.client.force_login(self.guest)
        url = reverse("bookings:create", args=[self.property.pk])
        data = {"check_in": self.check_in, "check_out": self.check_out, "guests": 2}

        first = self.client.post(url, data)
        self.assertRedirects(first, reverse("users:dashboard"))
        booking = Booking.objects.get()
        self.assertEqual(booking.total_price, Decimal("9600.00"))

        overlapping = self.client.post(url, {
            "check_in": self.check_in + timedelta(days=1),
            "check_out": self.check_out + timedelta(days=1),
            "guests": 1,
        })
        self.assertEqual(overlapping.status_code, 200)
        self.assertContains(overlapping, "Those dates are no longer available")
        self.assertEqual(Booking.objects.count(), 1)

    def test_guest_cannot_book_their_own_property(self):
        self.client.force_login(self.host)
        response = self.client.post(reverse("bookings:create", args=[self.property.pk]), {
            "check_in": self.check_in,
            "check_out": self.check_out,
            "guests": 1,
        })

        self.assertContains(response, "You can’t book your own place.")
        self.assertFalse(Booking.objects.exists())
