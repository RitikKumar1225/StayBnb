import builtins

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models

from properties.models import Property


class Booking(models.Model):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    STATUS_CHOICES = [(PENDING, "Pending"), (CONFIRMED, "Confirmed"), (CANCELLED, "Cancelled")]

    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name="bookings")
    guest = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="bookings")
    check_in = models.DateField()
    check_out = models.DateField()
    guests = models.PositiveSmallIntegerField(default=1, validators=[MinValueValidator(1)])
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default=PENDING)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.property} · {self.check_in} to {self.check_out}"

    @builtins.property
    def nights(self):
        return (self.check_out - self.check_in).days
