from django.contrib import admin
from django.urls import include, path

from accounts.views import home

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", home, name="home"),
    path("comptes/", include("accounts.urls")),
    path("dashboard/", include("dashboard.urls")),
    path("paiements/", include("payments.urls")),
    path("administration/", include("admin_panel.urls")),
]
