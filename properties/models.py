from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.urls import reverse


class Property(models.Model):
    APARTMENT = "apartment"
    HOUSE = "house"
    CABIN = "cabin"
    VILLA = "villa"
    TYPE_CHOICES = [
        (APARTMENT, "Apartment"),
        (HOUSE, "House"),
        (CABIN, "Cabin"),
        (VILLA, "Villa"),
    ]

    host = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="properties")
    title = models.CharField(max_length=180)
    description = models.TextField()
    location = models.CharField(max_length=180)
    property_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default=APARTMENT)
    price_per_night = models.DecimalField(max_digits=9, decimal_places=2, validators=[MinValueValidator(1)])
    cover_image = models.ImageField(upload_to="properties/", blank=True)
    cover_image_url = models.URLField(max_length=500, blank=True)
    amenities = models.CharField(max_length=500, blank=True, help_text="Separate amenities with commas.")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)
        verbose_name_plural = "properties"

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("properties:detail", kwargs={"pk": self.pk})

    @property
    def amenity_list(self):
        return [item.strip() for item in self.amenities.split(",") if item.strip()]


class PropertyImage(models.Model):
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="properties/")
    caption = models.CharField(max_length=120, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("uploaded_at",)

    def __str__(self):
        return f"Image for {self.property}"


@receiver(post_delete, sender=Property)
def remove_property_cover_image_file(sender, instance, **kwargs):
    if instance.cover_image:
        instance.cover_image.delete(save=False)


@receiver(post_delete, sender=PropertyImage)
def remove_property_image_file(sender, instance, **kwargs):
    if instance.image:
        instance.image.delete(save=False)
