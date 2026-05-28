from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    path("connexion/", views.SignInView.as_view(), name="signin"),
    path("activation/", views.activate_account, name="activate"),
    path("deconnexion/", views.SignOutView.as_view(), name="signout"),
]
