from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from properties.models import Property


class Review(models.Model):
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name="reviews")
    guest = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reviews")
    rating = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)
        constraints = [models.UniqueConstraint(fields=("property", "guest"), name="unique_review_per_guest_property")]

    def __str__(self):
        return f"{self.rating}/5 · {self.property}"
