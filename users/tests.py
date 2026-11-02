from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils import timezone

from bookings.models import Booking
from properties.models import Property
from .models import Profile


class AccountFlowTests(TestCase):
    def test_signup_creates_one_account_without_a_guest_or_host_role(self):
        signup_page = self.client.get(reverse("users:signup"))
        response = self.client.post(reverse("users:signup"), {
            "first_name": "Riya",
            "username": "riya",
            "email": "riya@example.com",
            "password1": "A-long-safe-passphrase-93",
            "password2": "A-long-safe-passphrase-93",
        })

        self.assertRedirects(response, reverse("users:dashboard"))
        user = User.objects.get(username="riya")
        self.assertEqual(self.client.session["_auth_user_id"], str(user.pk))
        self.assertTrue(Profile.objects.filter(user=user).exists())
        self.assertNotIn("role", signup_page.context["form"].fields)

    def test_same_dashboard_offers_booking_and_renting_options(self):
        user = User.objects.create_user(username="riya", password="test-password-123")
        self.client.force_login(user)

        response = self.client.get(reverse("users:dashboard"))

        self.assertContains(response, "Find a stay")
        self.assertContains(response, "List a place")
        self.assertContains(response, "YOUR TRIPS")
        self.assertContains(response, "Places you rent out")

    def test_same_account_dashboard_shows_its_booking_and_listing(self):
        user = User.objects.create_user(username="traveller-host", password="test-password-123")
        other_host = User.objects.create_user(username="other-host", password="test-password-123")
        own_listing = Property.objects.create(
            host=user,
            title="My rented place",
            description="A quiet home.",
            location="Shimla",
            price_per_night=3000,
        )
        booked_listing = Property.objects.create(
            host=other_host,
            title="A place I booked",
            description="A little getaway.",
            location="Goa",
            price_per_night=4000,
        )
        check_in = timezone.localdate() + timedelta(days=10)
        Booking.objects.create(
            property=booked_listing,
            guest=user,
            check_in=check_in,
            check_out=check_in + timedelta(days=2),
            guests=1,
            total_price=8000,
        )
        self.client.force_login(user)

        response = self.client.get(reverse("users:dashboard"))

        self.assertContains(response, own_listing.title)
        self.assertContains(response, booked_listing.title)

    def test_dashboard_redirects_anonymous_visitors_to_login(self):
        response = self.client.get(reverse("users:dashboard"))

        self.assertRedirects(response, f"{reverse('users:login')}?next={reverse('users:dashboard')}")
