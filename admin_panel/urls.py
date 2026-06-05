from django.urls import path

from . import views

app_name = "admin_panel"

urlpatterns = [
    path("connexion/", views.AdminLoginView.as_view(), name="login"),
    path("", views.DashboardAdminView.as_view(), name="index"),
    path("eleves/", views.ElevesAdminView.as_view(), name="eleves"),
    path("paiements/", views.PaiementsAdminView.as_view(), name="paiements"),
]
