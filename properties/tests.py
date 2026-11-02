from datetime import timedelta
from decimal import Decimal
from io import BytesIO

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from PIL import Image

from bookings.models import Booking
from reviews.models import Review
from properties.management.commands.seed_sample_data import SAMPLE_STAYS
from .models import Property, PropertyImage


class PropertyDiscoveryTests(TestCase):
    def setUp(self):
        self.host = User.objects.create_user(username="host", password="test-password-123")
        self.cabin = Property.objects.create(
            host=self.host,
            title="Pine Quiet",
            description="A quiet cabin among the trees.",
            location="Manali",
            property_type=Property.CABIN,
            price_per_night=4500,
        )
        Property.objects.create(
            host=self.host,
            title="City Light",
            description="A sunny city apartment.",
            location="Jaipur",
            property_type=Property.APARTMENT,
            price_per_night=6500,
        )

    def tearDown(self):
        for image in PropertyImage.objects.all():
            image.image.delete(save=False)
        for listing in Property.objects.all():
            listing.cover_image.delete(save=False)

    def test_search_filters_location_type_and_price(self):
        response = self.client.get(reverse("properties:home"), {
            "location": "man",
            "type": Property.CABIN,
            "max_price": "5000",
        })

        self.assertEqual(list(response.context["listings"]), [self.cabin])

    def test_property_detail_renders(self):
        response = self.client.get(self.cabin.get_absolute_url())

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Pine Quiet")
        self.assertContains(response, "Manali")
        self.assertContains(response, "data-availability-calendar")
        self.assertContains(response, "Guest reviews")

    def test_home_page_provides_show_more_control_for_property_rows(self):
        for index in range(10):
            Property.objects.create(
                host=self.host,
                title=f"Extra stay {index}",
                description="A lovely place.",
                location="Manali",
                price_per_night=Decimal("100.00"),
            )

        response = self.client.get(reverse("properties:home"))

        self.assertContains(response, 'data-place-grid')
        self.assertContains(response, 'data-place-card')
        self.assertContains(response, 'data-show-places')
        self.assertContains(response, "Show more places")

    def test_cover_photo_url_is_shown_in_property_and_user_dashboard_previews(self):
        self.cabin.cover_image_url = "https://images.example.test/cabin.jpg"
        self.cabin.save(update_fields=["cover_image_url"])
        home = self.client.get(reverse("properties:home"))
        self.assertContains(home, self.cabin.cover_image_url)

        self.client.force_login(self.host)
        dashboard = self.client.get(reverse("users:dashboard"))
        self.assertContains(dashboard, self.cabin.cover_image_url)

    def test_detail_page_calendar_marks_unavailable_booking_dates(self):
        today = timezone.localdate()
        Booking.objects.create(
            property=self.cabin,
            guest=User.objects.create_user(username="booked-guest", password="test-password-123"),
            check_in=today + timedelta(days=10),
            check_out=today + timedelta(days=13),
            guests=1,
            total_price=13500,
        )

        response = self.client.get(self.cabin.get_absolute_url())

        self.assertContains(response, "property-availability")
        self.assertContains(response, (today + timedelta(days=10)).isoformat())
        self.assertContains(response, "legend-busy")

    def test_guest_can_request_a_booking_from_property_detail(self):
        guest = User.objects.create_user(username="booking-guest", password="test-password-123")
        self.client.force_login(guest)
        check_in = timezone.localdate() + timedelta(days=20)

        response = self.client.post(self.cabin.get_absolute_url(), {
            "action": "book",
            "check_in": check_in.isoformat(),
            "check_out": (check_in + timedelta(days=2)).isoformat(),
            "guests": "2",
        })

        self.assertRedirects(response, self.cabin.get_absolute_url())
        booking = Booking.objects.get(property=self.cabin, guest=guest)
        self.assertEqual(booking.total_price, 9000)

    def test_regular_account_can_create_a_property_listing(self):
        self.client.force_login(self.host)

        response = self.client.get(reverse("properties:create"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Publish your place")
        self.assertContains(response, 'type="file" name="cover_image"')
        self.assertNotContains(response, "Cover photo URL")

    def test_inline_booking_rejects_booked_dates(self):
        guest = User.objects.create_user(username="booking-guest", password="test-password-123")
        existing_guest = User.objects.create_user(username="existing-guest", password="test-password-123")
        check_in = timezone.localdate() + timedelta(days=20)
        Booking.objects.create(
            property=self.cabin,
            guest=existing_guest,
            check_in=check_in,
            check_out=check_in + timedelta(days=3),
            guests=1,
            total_price=13500,
        )
        self.client.force_login(guest)

        response = self.client.post(self.cabin.get_absolute_url(), {
            "action": "book",
            "check_in": (check_in + timedelta(days=1)).isoformat(),
            "check_out": (check_in + timedelta(days=4)).isoformat(),
            "guests": "1",
        })

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Those dates are no longer available")
        self.assertEqual(Booking.objects.filter(property=self.cabin).count(), 1)

    def test_guest_can_review_on_detail_after_completed_confirmed_stay(self):
        guest = User.objects.create_user(username="review-guest", password="test-password-123")
        Booking.objects.create(
            property=self.cabin,
            guest=guest,
            check_in=timezone.localdate() - timedelta(days=4),
            check_out=timezone.localdate() - timedelta(days=2),
            guests=1,
            total_price=9000,
            status=Booking.CONFIRMED,
        )
        self.client.force_login(guest)

        response = self.client.post(self.cabin.get_absolute_url(), {
            "action": "review",
            "rating": "5",
            "comment": "A beautiful stay.",
        })

        self.assertRedirects(response, self.cabin.get_absolute_url())
        self.assertEqual(Review.objects.get(property=self.cabin, guest=guest).rating, 5)
        self.assertContains(self.client.get(self.cabin.get_absolute_url()), "A beautiful stay.")

    def test_guest_without_a_completed_booking_cannot_submit_review_on_detail(self):
        guest = User.objects.create_user(username="review-guest", password="test-password-123")
        self.client.force_login(guest)

        response = self.client.post(self.cabin.get_absolute_url(), {
            "action": "review",
            "rating": "5",
            "comment": "A review without a stay.",
        })

        self.assertRedirects(response, self.cabin.get_absolute_url())
        self.assertFalse(Review.objects.exists())

    def test_invalid_price_filter_does_not_break_discovery(self):
        response = self.client.get(reverse("properties:home"), {"min_price": "not-a-price"})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Enter a number")
        self.assertEqual(len(response.context["listings"]), 2)

    def test_host_can_publish_listing_with_multiple_images(self):
        self.client.force_login(self.host)
        image_data = BytesIO()
        Image.new("RGB", (12, 12), color="olive").save(image_data, format="JPEG")
        image_bytes = image_data.getvalue()
        response = self.client.post(reverse("properties:create"), {
            "title": "A little hideaway",
            "description": "A quiet place to land.",
            "location": "Coorg",
            "property_type": Property.CABIN,
            "price_per_night": "5400.00",
            "amenities": "Fireplace, Garden",
            "images": [
                SimpleUploadedFile("one.jpg", image_bytes, content_type="image/jpeg"),
                SimpleUploadedFile("two.jpg", image_bytes, content_type="image/jpeg"),
            ],
        })

        self.assertEqual(response.status_code, 302)
        images = PropertyImage.objects.filter(property__title="A little hideaway")
        self.assertEqual(images.count(), 2)
        removed_file = images.first().image.name

        response = self.client.post(reverse("properties:edit", args=[images.first().property_id]), {
            "title": "A little hideaway",
            "description": "A quiet place to land.",
            "location": "Coorg",
            "property_type": Property.CABIN,
            "price_per_night": "5400.00",
            "amenities": "Fireplace, Garden",
            "delete_images": [images.first().pk],
        })

        self.assertEqual(response.status_code, 302)
        self.assertEqual(PropertyImage.objects.filter(property__title="A little hideaway").count(), 1)
        self.assertFalse(images.first().image.storage.exists(removed_file))

    def test_host_can_upload_and_remove_a_local_cover_photo(self):
        self.client.force_login(self.host)
        image_data = BytesIO()
        Image.new("RGB", (12, 12), color="olive").save(image_data, format="JPEG")
        image_bytes = image_data.getvalue()
        response = self.client.post(reverse("properties:create"), {
            "title": "Local cover",
            "description": "A place.",
            "location": "Lisbon, Portugal",
            "property_type": Property.APARTMENT,
            "price_per_night": "100.00",
            "amenities": "",
            "cover_image": SimpleUploadedFile("cover.jpg", image_bytes, content_type="image/jpeg"),
        })

        self.assertEqual(response.status_code, 302)
        listing = Property.objects.get(title="Local cover")
        old_cover_name = listing.cover_image.name
        self.assertTrue(listing.cover_image.storage.exists(old_cover_name))
        edit_url = reverse("properties:edit", args=[listing.pk])
        self.assertContains(self.client.get(edit_url), "Remove cover photo")

        replacement_image = SimpleUploadedFile(
            "replacement.jpg",
            image_bytes,
            content_type="image/jpeg",
        )
        response = self.client.post(edit_url, {
            "title": listing.title,
            "description": listing.description,
            "location": listing.location,
            "property_type": listing.property_type,
            "price_per_night": listing.price_per_night,
            "amenities": listing.amenities,
            "cover_image": replacement_image,
        })

        self.assertEqual(response.status_code, 302)
        listing.refresh_from_db()
        replacement_cover_name = listing.cover_image.name
        self.assertNotEqual(replacement_cover_name, old_cover_name)
        self.assertFalse(listing.cover_image.storage.exists(old_cover_name))

        response = self.client.post(edit_url, {
            "title": listing.title,
            "description": listing.description,
            "location": listing.location,
            "property_type": listing.property_type,
            "price_per_night": listing.price_per_night,
            "amenities": listing.amenities,
            "delete_cover_photo": "1",
        })

        self.assertEqual(response.status_code, 302)
        listing.refresh_from_db()
        self.assertFalse(listing.cover_image)
        self.assertFalse(listing.cover_image.storage.exists(replacement_cover_name))

    def test_deleting_a_property_removes_its_local_cover_file(self):
        image_data = BytesIO()
        Image.new("RGB", (12, 12), color="olive").save(image_data, format="JPEG")
        listing = Property.objects.create(
            host=self.host,
            title="Cover cleanup",
            description="A place.",
            location="Lisbon, Portugal",
            price_per_night=Decimal("100.00"),
            cover_image=SimpleUploadedFile(
                "delete-cover.jpg",
                image_data.getvalue(),
                content_type="image/jpeg",
            ),
        )
        cover_name = listing.cover_image.name

        listing.delete()

        self.assertFalse(listing.cover_image.storage.exists(cover_name))


class SampleDataCommandTests(TestCase):
    def test_command_creates_international_stays_idempotently(self):
        call_command("seed_sample_data")

        sample_host = User.objects.get(username="staybnb-sample-host")
        sample_listings = Property.objects.filter(host=sample_host)
        self.assertEqual(sample_listings.count(), len(SAMPLE_STAYS))
        self.assertTrue(all(listing.cover_image_url for listing in sample_listings))
        self.assertEqual(
            len(set(sample_listings.values_list("cover_image_url", flat=True))),
            len(SAMPLE_STAYS),
        )
        self.assertTrue(all(listing.price_per_night < 1000 for listing in sample_listings))
        self.assertFalse(
            sample_listings.filter(location__iregex=r"(india|rajasthan|uttarakhand|himachal|tamil nadu)").exists()
        )
        property_to_book = sample_listings.get(title="The Cedar House")
        guest = User.objects.create_user(username="sample-booking-guest", password="test-password-123")
        check_in = timezone.localdate() + timedelta(days=20)
        booking = Booking.objects.create(
            property=property_to_book,
            guest=guest,
            check_in=check_in,
            check_out=check_in + timedelta(days=2),
            guests=1,
            total_price=Decimal("100000.00"),
        )
        call_command("seed_sample_data")
        self.assertEqual(Property.objects.filter(host=sample_host).count(), len(SAMPLE_STAYS))
        booking.refresh_from_db()
        self.assertEqual(booking.total_price, Decimal("100000.00"))
        self.assertContains(self.client.get(reverse("properties:home")), "$285.00")

    def test_command_keeps_transferred_sample_stays_with_the_new_host(self):
        call_command("seed_sample_data")
        former_host = User.objects.get(username="staybnb-sample-host")
        new_host = User.objects.create_user(
            username="new-host",
            email="new-host@example.com",
            password="test-password-123",
        )
        Property.objects.filter(host=former_host).update(host=new_host)
        former_host.delete()

        call_command("seed_sample_data")

        self.assertFalse(User.objects.filter(username="staybnb-sample-host").exists())
        self.assertEqual(Property.objects.filter(host=new_host).count(), len(SAMPLE_STAYS))
        self.assertEqual(Property.objects.count(), len(SAMPLE_STAYS))
