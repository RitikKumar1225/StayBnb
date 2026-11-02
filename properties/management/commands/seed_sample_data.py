from datetime import timedelta
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Count
from django.utils import timezone

from bookings.models import Booking
from properties.models import Property
from reviews.models import Review
from users.models import Profile


SAMPLE_STAYS = [
    {
        "title": "The Cedar House",
        "description": "A timber cabin among the pines with a wood stove, a slow breakfast, and mountain trails just beyond the gate. Come for the fresh air; stay for the quiet.",
        "location": "Aspen, Colorado, USA",
        "property_type": Property.CABIN,
        "price_per_night": 285,
        "amenities": "Wood stove, Mountain view, Kitchen, Wi-Fi",
        "cover_image_url": "https://images.unsplash.com/photo-1449158743715-0a90ebb6d2d8?auto=format&fit=crop&w=1000&q=85",
    },
    {
        "title": "A Courtyard in the Pink City",
        "description": "A calm, light-filled riad in the rose-colored medina, with hand-painted details and a leafy courtyard made for mint tea. The old souks are just around the corner.",
        "location": "Marrakech, Morocco",
        "property_type": Property.HOUSE,
        "price_per_night": 165,
        "amenities": "Private courtyard, Air conditioning, Breakfast, Wi-Fi",
        "cover_image_url": "https://images.unsplash.com/photo-1539020140153-e479b8c22e70?auto=format&fit=crop&w=1000&q=85",
    },
    {
        "title": "Salt Air, Slow Days",
        "description": "A whitewashed villa on a quiet lane near the Atlantic. Spend the afternoon under the palms, then wander out for grilled fish as the sky turns pink.",
        "location": "Lagos, Algarve, Portugal",
        "property_type": Property.VILLA,
        "price_per_night": 320,
        "amenities": "Plunge pool, Garden, Kitchen, Air conditioning",
        "cover_image_url": "https://images.unsplash.com/photo-1613490493576-7fde63acd811?auto=format&fit=crop&w=1000&q=85",
    },
    {
        "title": "The Old Bookshop Loft",
        "description": "Above a little second-hand bookshop, this generous loft pairs old wood floors with tall Georgian windows. Independent cafés, galleries, and the tram are all close by.",
        "location": "Edinburgh, Scotland",
        "property_type": Property.APARTMENT,
        "price_per_night": 210,
        "amenities": "City view, Workspace, Elevator, Wi-Fi",
        "cover_image_url": "https://images.unsplash.com/photo-1600210492486-724fe5c67fb0?auto=format&fit=crop&w=1000&q=85",
    },
    {
        "title": "Pineside, with a View",
        "description": "A small, design-minded hideaway above a forested valley. There is a reading nook for rainy hours and a balcony for the first cup of coffee.",
        "location": "Black Forest, Germany",
        "property_type": Property.CABIN,
        "price_per_night": 195,
        "amenities": "Valley view, Balcony, Reading nook, Heating",
        "cover_image_url": "https://images.unsplash.com/photo-1510798831971-661eb04b3739?auto=format&fit=crop&w=1000&q=85",
    },
    {
        "title": "The Sunday House",
        "description": "A roomy, sun-washed home with a long dining table and space for everyone to linger. Pick up something fresh at the market, then watch the light change over the mountain.",
        "location": "Cape Town, South Africa",
        "property_type": Property.HOUSE,
        "price_per_night": 240,
        "amenities": "Garden, Full kitchen, Board games, Free parking",
        "cover_image_url": "https://images.unsplash.com/photo-1600607687939-ce8a6c25118c?auto=format&fit=crop&w=1000&q=85",
    },
    {
        "title": "The Little Canal House",
        "description": "A quietly restored canal-side home with a bright kitchen and room to leave your bike. Slow mornings, market flowers, and the whole city on foot.",
        "location": "Amsterdam, Netherlands",
        "property_type": Property.HOUSE,
        "price_per_night": 275,
        "amenities": "Canal view, Kitchen, Bicycle storage, Wi-Fi",
        "cover_image_url": "https://images.unsplash.com/photo-1511818966892-d7d671e672a2?auto=format&fit=crop&w=1000&q=85",
    },
    {
        "title": "A Room Above the Lanterns",
        "description": "A warm, thoughtfully layered apartment on a tucked-away Tokyo lane. Find ramen after dark, then come home to soft light and a deep soaking tub.",
        "location": "Kyoto, Japan",
        "property_type": Property.APARTMENT,
        "price_per_night": 185,
        "amenities": "Soaking tub, Tea set, Air conditioning, Wi-Fi",
        "cover_image_url": "https://images.unsplash.com/photo-1493976040374-85c8e12f0c0e?auto=format&fit=crop&w=1000&q=85",
    },
    {
        "title": "The Aegean Blue House",
        "description": "A little whitewashed home above the water, with a shaded terrace for long lunches and a path down to a quiet cove.",
        "location": "Naxos, Greece",
        "property_type": Property.HOUSE,
        "price_per_night": 230,
        "amenities": "Sea view, Terrace, Full kitchen, Outdoor shower",
        "cover_image_url": "https://images.unsplash.com/photo-1533105079780-92b9be482077?auto=format&fit=crop&w=1000&q=85",
    },
    {
        "title": "A Loft in the Marais",
        "description": "An airy old-world loft with tall windows and a little library. Step outside for a morning croissant, a museum afternoon, and dinner that runs late.",
        "location": "Paris, France",
        "property_type": Property.APARTMENT,
        "price_per_night": 295,
        "amenities": "Workspace, Washer, Elevator, Walkable neighborhood",
        "cover_image_url": "https://images.unsplash.com/photo-1502602898657-3e91760cbb34?auto=format&fit=crop&w=1000&q=85",
    },
    {
        "title": "The High Desert Casita",
        "description": "Adobe walls, open skies, and a deep porch for watching the desert settle at dusk. A peaceful base for art, hikes, and a very good long weekend.",
        "location": "Santa Fe, New Mexico, USA",
        "property_type": Property.HOUSE,
        "price_per_night": 205,
        "amenities": "Private patio, Fireplace, Kitchen, Free parking",
        "cover_image_url": "https://images.unsplash.com/photo-1600607687920-4e2a09cf159d?auto=format&fit=crop&w=1000&q=85",
    },
    {
        "title": "The Seaside Reading Room",
        "description": "A bright coastal cottage with books in every corner and the shoreline just down the lane. Bring a sweater, a stack of paperbacks, and nowhere to be.",
        "location": "Cornwall, England",
        "property_type": Property.CABIN,
        "price_per_night": 175,
        "amenities": "Sea view, Books, Wood stove, Garden",
        "cover_image_url": "https://images.unsplash.com/photo-1600566753086-00f18fb6b3ea?auto=format&fit=crop&w=1000&q=85",
    },
]

SAMPLE_GUESTS = [
    {
        "username": "maya_lin",
        "first_name": "Maya Lin",
        "email": "maya@example.com",
        "bio": "Architectural photographer and weekend trail runner.",
    },
    {
        "username": "liam_vance",
        "first_name": "Liam Vance",
        "email": "liam@example.com",
        "bio": "Lover of cozy cabins, hot tea, and snowy mornings.",
    },
    {
        "username": "elena_rostova",
        "first_name": "Elena Rostova",
        "email": "elena@example.com",
        "bio": "Writer traveling slowly between cities and mountain towns.",
    },
    {
        "username": "sofia_chen",
        "first_name": "Sofia Chen",
        "email": "sofia@example.com",
        "bio": "Curator exploring vernacular architecture and courtyard gardens.",
    },
    {
        "username": "noah_becker",
        "first_name": "Noah Becker",
        "email": "noah@example.com",
        "bio": "Surfer and freelance designer chasing coastal light.",
    },
    {
        "username": "clara_campbell",
        "first_name": "Clara Campbell",
        "email": "clara@example.com",
        "bio": "Book editor with an affinity for historic lofts and espresso.",
    },
    {
        "username": "david_kim",
        "first_name": "David Kim",
        "email": "david@example.com",
        "bio": "Hiker and sound recordist exploring forest quietude.",
    },
    {
        "username": "chloe_dubois",
        "first_name": "Chloe Dubois",
        "email": "chloe@example.com",
        "bio": "Chef who loves farmers markets and long dinner tables.",
    },
    {
        "username": "marcus_thorne",
        "first_name": "Marcus Thorne",
        "email": "marcus@example.com",
        "bio": "Urban cyclist and historian always exploring on foot.",
    },
    {
        "username": "aisha_patel",
        "first_name": "Aisha Patel",
        "email": "aisha@example.com",
        "bio": "Travel writer drawn to tranquil gardens and lantern-lit lanes.",
    },
]

SAMPLE_REVIEWS = [
    # The Cedar House (Aspen, Colorado)
    {
        "property_title": "The Cedar House",
        "guest_username": "maya_lin",
        "rating": 5,
        "days_ago": 45,
        "comment": "The wood stove was already glowing when we arrived after a chilly drive into Aspen. Waking up to panoramic mountain views through the tall pines was pure magic. Unbelievably peaceful, beautifully equipped kitchen, and super fast Wi-Fi.",
    },
    {
        "property_title": "The Cedar House",
        "guest_username": "liam_vance",
        "rating": 5,
        "days_ago": 24,
        "comment": "Hands down the best cabin stay we've ever had in Colorado. The timber craftsmanship is stunning, the bed is cozy, and mountain trails start right outside the back gate. Our mornings with hot coffee on the porch were unforgettable.",
    },
    {
        "property_title": "The Cedar House",
        "guest_username": "elena_rostova",
        "rating": 5,
        "days_ago": 9,
        "comment": "Crisp mountain air, absolute silence at night, and stunning starry skies. The wood stove keeps the entire place toasty warm. A truly restorative retreat from city life.",
    },
    # A Courtyard in the Pink City (Marrakech)
    {
        "property_title": "A Courtyard in the Pink City",
        "guest_username": "sofia_chen",
        "rating": 5,
        "days_ago": 35,
        "comment": "Drinking fresh mint tea in the leafy courtyard while listening to birds in the morning was heavenly. Close to the vibrant souks yet an oasis of absolute calm.",
    },
    {
        "property_title": "A Courtyard in the Pink City",
        "guest_username": "aisha_patel",
        "rating": 5,
        "days_ago": 15,
        "comment": "The hand-painted tiles and gentle courtyard breeze made our stay unforgettable. The host gave incredible recommendations for local tagine and tucked-away spice shops.",
    },
    # Salt Air, Slow Days (Lagos, Portugal)
    {
        "property_title": "Salt Air, Slow Days",
        "guest_username": "noah_becker",
        "rating": 5,
        "days_ago": 38,
        "comment": "The plunge pool under the palms was our favorite spot after long beach mornings. The villa is spotless, airy, and within an easy wander to grilled fresh fish at the marina.",
    },
    {
        "property_title": "Salt Air, Slow Days",
        "guest_username": "liam_vance",
        "rating": 5,
        "days_ago": 18,
        "comment": "Sun-drenched, tranquil, and beautifully styled. Walking down to the Atlantic cliffs at sunset was breathtaking.",
    },
    # The Old Bookshop Loft (Edinburgh)
    {
        "property_title": "The Old Bookshop Loft",
        "guest_username": "clara_campbell",
        "rating": 5,
        "days_ago": 30,
        "comment": "A bibliophile's dream loft! High ceilings, lovely Georgian windows overlooking the street, and independent bakeries just down the cobblestones.",
    },
    {
        "property_title": "The Old Bookshop Loft",
        "guest_username": "david_kim",
        "rating": 5,
        "days_ago": 12,
        "comment": "The light pouring through the tall windows in the afternoon is unmatched. Great workspace and wonderful café culture right outside the door.",
    },
    # Pineside, with a View (Black Forest)
    {
        "property_title": "Pineside, with a View",
        "guest_username": "david_kim",
        "rating": 5,
        "days_ago": 40,
        "comment": "The reading nook by the window is everything. We spent hours reading while rain tapped against the glass. Quiet, scenic, and deeply comforting.",
    },
    {
        "property_title": "Pineside, with a View",
        "guest_username": "maya_lin",
        "rating": 5,
        "days_ago": 16,
        "comment": "Breathtaking valley views and endless forest paths. The first cup of coffee on that balcony was the highlight of our vacation.",
    },
    # The Sunday House (Cape Town)
    {
        "property_title": "The Sunday House",
        "guest_username": "chloe_dubois",
        "rating": 5,
        "days_ago": 33,
        "comment": "Stunning light from morning till sunset with Table Mountain right behind. The kitchen had everything for big family dinners after shopping the local market.",
    },
    {
        "property_title": "The Sunday House",
        "guest_username": "marcus_thorne",
        "rating": 5,
        "days_ago": 14,
        "comment": "Roomy, warm, and inviting. The garden is wonderful for afternoon reading and watching the clouds roll over the peaks.",
    },
    # The Little Canal House (Amsterdam)
    {
        "property_title": "The Little Canal House",
        "guest_username": "marcus_thorne",
        "rating": 5,
        "days_ago": 28,
        "comment": "Waking up right along the canal with bikes leaning against the bridge was the quintessential Amsterdam experience. Walkable to everything.",
    },
    {
        "property_title": "The Little Canal House",
        "guest_username": "sofia_chen",
        "rating": 5,
        "days_ago": 8,
        "comment": "Bright, thoughtfully restored, and so charming. Having coffee by the canal windows each morning made us feel like locals.",
    },
    # A Room Above the Lanterns (Kyoto)
    {
        "property_title": "A Room Above the Lanterns",
        "guest_username": "aisha_patel",
        "rating": 5,
        "days_ago": 34,
        "comment": "The deep wooden soaking tub after walking 20,000 steps around Kyoto temples was pure bliss. The tea set and serene lanterns made this extraordinary.",
    },
    {
        "property_title": "A Room Above the Lanterns",
        "guest_username": "clara_campbell",
        "rating": 5,
        "days_ago": 11,
        "comment": "A peaceful sanctuary in Kyoto. Soft lighting, wonderful tatami textures, and incredible ramen stalls hidden just around the corner.",
    },
    # The Aegean Blue House (Naxos)
    {
        "property_title": "The Aegean Blue House",
        "guest_username": "elena_rostova",
        "rating": 5,
        "days_ago": 42,
        "comment": "Watching the sun dip into the Aegean from the shaded terrace with local cheese and olives was paradise. The cove down the path is crystal clear.",
    },
    {
        "property_title": "The Aegean Blue House",
        "guest_username": "noah_becker",
        "rating": 5,
        "days_ago": 21,
        "comment": "The outdoor shower under the Greek sun after a morning swim is perfection. Simple, whitewashed beauty at its finest.",
    },
    # A Loft in the Marais (Paris)
    {
        "property_title": "A Loft in the Marais",
        "guest_username": "chloe_dubois",
        "rating": 5,
        "days_ago": 29,
        "comment": "Step outside right into the heart of Le Marais. Fresh croissants every morning, beautiful art books in the loft, and wonderful natural light.",
    },
    {
        "property_title": "A Loft in the Marais",
        "guest_username": "elena_rostova",
        "rating": 5,
        "days_ago": 7,
        "comment": "High ceilings, charming Parisian views, and an elevator that makes luggage easy. The neighborhood is vibrant and full of galleries.",
    },
    # The High Desert Casita (Santa Fe)
    {
        "property_title": "The High Desert Casita",
        "guest_username": "maya_lin",
        "rating": 5,
        "days_ago": 36,
        "comment": "The adobe fireplace at twilight is unmatched. Stunning Santa Fe sunsets, quiet desert breeze, and gorgeous handcrafted textiles throughout.",
    },
    {
        "property_title": "The High Desert Casita",
        "guest_username": "liam_vance",
        "rating": 5,
        "days_ago": 13,
        "comment": "Peaceful, authentic, and cozy. Sitting on the porch watching the sky turn purple over the desert mountains was a memory we'll treasure.",
    },
    # The Seaside Reading Room (Cornwall)
    {
        "property_title": "The Seaside Reading Room",
        "guest_username": "clara_campbell",
        "rating": 5,
        "days_ago": 31,
        "comment": "The book collection is extraordinary. Sweaters, wood fire crackling, and hot tea with the sea crashing down the lane. Pure coastal bliss.",
    },
    {
        "property_title": "The Seaside Reading Room",
        "guest_username": "david_kim",
        "rating": 5,
        "days_ago": 17,
        "comment": "If you need to rest, think, or read, this is the place. You can hear the ocean from the garden. We didn't want to leave.",
    },
]


class Command(BaseCommand):
    help = "Create or update international sample stays, guest profiles, completed stays, and reviews."

    @transaction.atomic
    def handle(self, *args, **options):
        User = get_user_model()
        today = timezone.localdate()
        now = timezone.now()

        sample_titles = [stay["title"] for stay in SAMPLE_STAYS]
        existing_sample_owner = (
            Property.objects.filter(title__in=sample_titles)
            .values("host_id")
            .annotate(listing_count=Count("id"))
            .order_by("-listing_count")
            .first()
        )
        if existing_sample_owner:
            host = User.objects.get(pk=existing_sample_owner["host_id"])
            Profile.objects.get_or_create(user=host)
        else:
            host, _ = User.objects.get_or_create(
                username="staybnb-sample-host",
                defaults={
                    "first_name": "Aarav",
                    "email": "sample-host@example.com",
                },
            )
            Profile.objects.get_or_create(
                user=host,
                defaults={
                    "bio": "A local host who loves thoughtful spaces and sharing favorite neighborhood spots.",
                },
            )

        properties_by_title = {}
        created_count = 0
        for stay in SAMPLE_STAYS:
            prop, created = Property.objects.update_or_create(
                host=host,
                title=stay["title"],
                defaults=stay,
            )
            properties_by_title[stay["title"]] = prop
            created_count += int(created)

        # Create or update sample guests
        guests_by_username = {}
        for guest_data in SAMPLE_GUESTS:
            guest, _ = User.objects.get_or_create(
                username=guest_data["username"],
                defaults={
                    "first_name": guest_data["first_name"],
                    "email": guest_data["email"],
                },
            )
            Profile.objects.get_or_create(
                user=guest,
                defaults={"bio": guest_data["bio"]},
            )
            guests_by_username[guest_data["username"]] = guest

        # Create completed bookings and reviews
        reviews_added = 0
        for item in SAMPLE_REVIEWS:
            prop = properties_by_title.get(item["property_title"])
            guest = guests_by_username.get(item["guest_username"])
            if not prop or not guest:
                continue

            days_ago = item.get("days_ago", 14)
            check_out_date = today - timedelta(days=days_ago)
            check_in_date = check_out_date - timedelta(days=3)
            review_timestamp = now - timedelta(days=days_ago)

            # Ensure a confirmed past completed booking exists for this guest and property
            booking, _ = Booking.objects.get_or_create(
                property=prop,
                guest=guest,
                defaults={
                    "check_in": check_in_date,
                    "check_out": check_out_date,
                    "guests": 2,
                    "total_price": prop.price_per_night * 3,
                    "status": Booking.CONFIRMED,
                },
            )

            # Create or update the review
            review, rev_created = Review.objects.update_or_create(
                property=prop,
                guest=guest,
                defaults={
                    "rating": item["rating"],
                    "comment": item["comment"],
                },
            )
            # Update created_at timestamp to match the historical stay
            Review.objects.filter(pk=review.pk).update(created_at=review_timestamp)

            if rev_created:
                reviews_added += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Sample listings ready. Added {created_count}; "
                f"there are now {len(SAMPLE_STAYS)} stays with {len(SAMPLE_REVIEWS)} guest reviews (added {reviews_added})."
            )
        )
