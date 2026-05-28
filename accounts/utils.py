from django.shortcuts import render

from .models import Eleve


def normalize_identifiant(value):
    return " ".join(value.strip().split()).upper()


def get_eleve_for_user(user):
    try:
        return Eleve.objects.select_related("classe", "user").get(user=user)
    except Eleve.DoesNotExist:
        return None


def render_no_eleve_profile(request):
    return render(request, "accounts/no_eleve_profile.html", status=403)
