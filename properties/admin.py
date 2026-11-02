from django.contrib import admin

from .models import Property, PropertyImage


class PropertyImageInline(admin.TabularInline):
    model = PropertyImage
    extra = 0


@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    list_display = ("title", "host", "location", "property_type", "price_per_night")
    list_filter = ("property_type", "location")
    search_fields = ("title", "location", "host__username")
    inlines = (PropertyImageInline,)
