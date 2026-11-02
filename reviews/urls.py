from django.urls import path

from . import views

app_name = "reviews"

urlpatterns = [path("new/<int:property_id>/", views.create, name="create")]
