from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.utils import timezone

from bookings.models import Booking
from properties.models import Property
from .forms import ProfileForm, SignUpForm
from .models import Profile


def signup(request):
    if request.user.is_authenticated:
        return redirect("users:dashboard")
    form = SignUpForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, "Welcome in. Your next good stay starts here.")
        return redirect("users:dashboard")
    return render(request, "users/signup.html", {"form": form})


@login_required
def dashboard(request):
    Profile.objects.get_or_create(user=request.user)
    bookings = (
        Booking.objects.filter(guest=request.user)
        .select_related("property")
        .prefetch_related("property__images")
        .order_by("-created_at")
    )
    listings = Property.objects.filter(host=request.user).prefetch_related("images")
    guest_requests = (
        Booking.objects.filter(property__host=request.user)
        .select_related("property", "guest")
        .order_by("-created_at")
    )
    return render(request, "users/guest_dashboard.html", {
        "bookings": bookings,
        "listings": listings,
        "guest_requests": guest_requests,
        "today": timezone.localdate(),
    })


@login_required
def profile(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)
    form = ProfileForm(request.POST or None, instance=profile)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Your profile has been updated.")
        return redirect("users:dashboard")
    return render(request, "users/profile.html", {"form": form})
