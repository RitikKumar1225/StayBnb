from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from bookings.models import Booking
from properties.models import Property
from .models import Review


class ReviewEligibilityTests(TestCase):
    def setUp(self):
        self.host = User.objects.create_user(username="host", password="test-password-123")
        self.guest = User.objects.create_user(username="guest", password="test-password-123")
        self.property = Property.objects.create(
            host=self.host,
            title="Quiet Morning",
            description="A restful stay.",
            location="Shimla",
            price_per_night=2500,
        )
        self.booking = Booking.objects.create(
            property=self.property,
            guest=self.guest,
            check_in=timezone.localdate() - timedelta(days=5),
            check_out=timezone.localdate() - timedelta(days=2),
            guests=1,
            total_price=7500,
            status=Booking.CONFIRMED,
        )

    def test_guest_can_review_after_a_confirmed_completed_stay_once(self):
        self.client.force_login(self.guest)
        url = reverse("reviews:create", args=[self.property.pk])

        response = self.client.post(url, {"rating": 5, "comment": "A lovely, quiet stay."})

        self.assertRedirects(response, self.property.get_absolute_url())
        self.assertEqual(Review.objects.get().guest, self.guest)
        self.client.post(url, {"rating": 4, "comment": "Another review."})
        self.assertEqual(Review.objects.count(), 1)

    def test_pending_booking_cannot_be_reviewed(self):
        self.booking.status = Booking.PENDING
        self.booking.save(update_fields=["status"])
        self.client.force_login(self.guest)

        response = self.client.get(reverse("reviews:create", args=[self.property.pk]))

        self.assertRedirects(response, self.property.get_absolute_url())
        self.assertFalse(Review.objects.exists())
