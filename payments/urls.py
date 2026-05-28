from django.urls import path

from . import views

app_name = "payments"

urlpatterns = [
    path("", views.liste_paiements, name="liste"),
    path("nouveau/", views.effectuer_paiement, name="nouveau"),
    path("<int:pk>/recu/", views.recu, name="recu"),
]
