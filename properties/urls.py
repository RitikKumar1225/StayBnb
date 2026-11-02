from django.urls import path

from . import views

app_name = "properties"

urlpatterns = [
    path("", views.home, name="home"),
    path("places/<int:pk>/", views.detail, name="detail"),
    path("host/places/new/", views.create, name="create"),
    path("host/places/<int:pk>/edit/", views.edit, name="edit"),
    path("host/places/<int:pk>/delete/", views.delete, name="delete"),
]
