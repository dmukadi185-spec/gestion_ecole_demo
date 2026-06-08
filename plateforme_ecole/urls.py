from django.contrib import admin
from django.urls import include, path

from accounts.views import home


def _superuser_only(self, request):
    return request.user.is_active and request.user.is_superuser


admin.site.__class__.has_permission = _superuser_only

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", home, name="home"),
    path("comptes/", include("accounts.urls")),
    path("dashboard/", include("dashboard.urls")),
    path("paiements/", include("payments.urls")),
    path("administration/", include("admin_panel.urls")),
    path("direction/", include("direction.urls")),
]
