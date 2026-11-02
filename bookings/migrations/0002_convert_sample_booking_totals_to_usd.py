from django.db import migrations


SAMPLE_TITLES = (
    "The Cedar House",
    "A Courtyard in the Pink City",
    "Salt Air, Slow Days",
    "The Old Bookshop Loft",
    "Pineside, with a View",
    "The Sunday House",
)


def convert_sample_booking_totals(apps, schema_editor):
    Booking = apps.get_model("bookings", "Booking")
    Property = apps.get_model("properties", "Property")
    database = schema_editor.connection.alias

    sample_properties = Property.objects.using(database).filter(
        title__in=SAMPLE_TITLES,
        cover_image_url__gt="",
    )
    for booking in Booking.objects.using(database).filter(
        property_id__in=sample_properties.values("pk"),
    ).select_related("property"):
        booking.total_price = booking.property.price_per_night * (booking.check_out - booking.check_in).days
        booking.save(using=database, update_fields=("total_price",))


class Migration(migrations.Migration):

    dependencies = [
        ("bookings", "0001_initial"),
        ("properties", "0003_property_cover_image_url"),
    ]

    operations = [
        migrations.RunPython(convert_sample_booking_totals, migrations.RunPython.noop),
    ]
