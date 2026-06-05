from django.urls import path

from . import views

app_name = "direction"

urlpatterns = [
    path("connexion/", views.DirecteurLoginView.as_view(), name="login"),
    path("", views.DashboardDirecteurView.as_view(), name="index"),
    path("finances/", views.FinancesDirecteurView.as_view(), name="finances"),
    path("eleves/", views.ElevesDirecteurView.as_view(), name="eleves"),
]
