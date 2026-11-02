from django.urls import path

from . import views

app_name = "bookings"

urlpatterns = [
    path("new/<int:property_id>/", views.create, name="create"),
    path("<int:pk>/cancel/", views.cancel, name="cancel"),
    path("<int:pk>/status/", views.update_status, name="update_status"),
]
