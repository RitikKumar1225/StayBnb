from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Count

from properties.models import Property
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


class Command(BaseCommand):
    help = "Create or update international sample stays for the homepage."

    @transaction.atomic
    def handle(self, *args, **options):
        User = get_user_model()
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

        created_count = 0
        for stay in SAMPLE_STAYS:
            _, created = Property.objects.update_or_create(
                host=host,
                title=stay["title"],
                defaults=stay,
            )
            created_count += int(created)

        self.stdout.write(
            self.style.SUCCESS(
                f"Sample listings ready. Added {created_count}; "
                f"there are now {len(SAMPLE_STAYS)} sample stays."
            )
        )
