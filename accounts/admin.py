from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.core.exceptions import ValidationError
from django.utils.html import format_html

from .models import Classe, Eleve, User
from .utils import normalize_identifiant


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ("identifiant", "is_active", "is_staff", "password_created")
    list_filter = ("is_active", "is_staff", "password_created")
    search_fields = ("identifiant",)
    ordering = ("identifiant",)

    fieldsets = (
        (None, {"fields": ("identifiant", "password")}),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "password_created",
                    "groups",
                    "user_permissions",
                )
            },
        ),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("identifiant", "is_active", "is_staff", "password_created"),
            },
        ),
    )

    def save_model(self, request, obj, form, change):
        if obj.identifiant:
            obj.identifiant = normalize_identifiant(obj.identifiant)
        super().save_model(request, obj, form, change)


@admin.register(Classe)
class ClasseAdmin(admin.ModelAdmin):
    list_display = ("niveau", "departement")
    search_fields = ("niveau", "departement")


@admin.register(Eleve)
class EleveAdmin(admin.ModelAdmin):
    list_display = ("nom", "postnom", "prenom", "identifiant_display", "classe")
    list_filter = ("classe",)
    search_fields = ("nom", "postnom", "prenom", "user__identifiant")
    autocomplete_fields = ("classe",)
    readonly_fields = ("identifiant_display",)
    fields = ("nom", "postnom", "prenom", "classe", "identifiant_display")

    @admin.display(description="Identifiant")
    def identifiant_display(self, obj):
        if obj.pk and obj.user_id:
            return obj.user.identifiant
        if obj.nom or obj.postnom or obj.prenom:
            preview = Eleve.generate_identifiant(obj.nom, obj.postnom, obj.prenom)
            return format_html(
                '<span title="Généré automatiquement à l\'enregistrement">{} (aperçu)</span>',
                preview,
            )
        return "— (nom + postnom + prénom en majuscules)"

    def get_fields(self, request, obj=None):
        return self.fields

    def save_model(self, request, obj, form, change):
        identifiant = Eleve.generate_identifiant(obj.nom, obj.postnom, obj.prenom)
        if not identifiant:
            self.message_user(
                request,
                "Le nom, le postnom et le prénom sont requis pour générer l'identifiant.",
                messages.ERROR,
            )
            return

        if not change:
            if User.objects.filter(identifiant=identifiant).exists():
                self.message_user(
                    request,
                    f"L'identifiant « {identifiant} » existe déjà. "
                    "Vérifiez les noms ou modifiez l'élève existant.",
                    messages.ERROR,
                )
                return
            obj.user = User.objects.create_user(identifiant=identifiant, is_active=True)
        else:
            try:
                obj.sync_user_identifiant()
            except ValidationError as exc:
                self.message_user(request, str(exc), messages.ERROR)
                return

        super().save_model(request, obj, form, change)
