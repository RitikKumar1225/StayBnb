# StayBnb

A small, server-rendered property rental platform built with Django, SQLite, Django Templates, Bootstrap 5, and vanilla JavaScript.

## Run locally

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Open `http://127.0.0.1:8000/`. Django Admin is at `/admin/`.

Populate the homepage with example stays by running:

```bash
python manage.py seed_sample_data
```

The command is safe to run more than once; it creates or updates international example listings.

## Features

- Single-account registration, login, logout, and profile management; every user can book stays and list places.
- A combined dashboard for your stays, listings, and guest booking requests.
- Property creation, editing, deletion, amenities, and multiple image uploads for hosts.
- Location, property type, and nightly price filters.
- Date-based booking requests with an on-page availability calendar, booked/past date indicators, overlap checks, host approval/cancellation, and guest dashboards.
- On-page reviews for confirmed bookings after checkout; one review per guest and property.
- Admin management for profiles, properties, property images, bookings, and reviews.

All prices are displayed in US dollars (USD). The 12 sample listings are international destinations and use distinct remote Unsplash cover photos. Hosts can upload photos or enter an HTTPS cover photo URL; uploaded property images are served from the local `media/` directory while `DEBUG` is enabled.

## Before deployment

Set `DJANGO_SECRET_KEY` to a unique secret, set `DJANGO_DEBUG=false`, configure `DJANGO_ALLOWED_HOSTS` as a comma-separated list, use a production web server for static and uploaded media, and review the security settings for your hosting environment.
