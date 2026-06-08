from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.core.exceptions import ValidationError
from django.utils.html import format_html

from .models import Classe, Directeur, Eleve, Professeur, User
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


@admin.register(Directeur)
class DirecteurAdmin(admin.ModelAdmin):
    list_display = ("nom_display", "titre", "identifiant_display", "compte_actif")
    list_filter = ("titre",)
    search_fields = ("nom", "postnom", "prenom", "user__identifiant")
    fields = ("titre", "nom", "postnom", "prenom")
    readonly_fields = ("compte_actif",)

    def get_fields(self, request, obj=None):
        if obj:
            return ("titre", "nom", "postnom", "prenom")
        return ("identifiant_input", "password_input", "titre", "nom", "postnom", "prenom")

    def get_form(self, request, obj=None, **kwargs):
        from django import forms

        class DirecteurForm(forms.ModelForm):
            identifiant_input = forms.CharField(
                label="Identifiant de connexion",
                required=True,
                help_text="Identifiant unique pour se connecter (ex : DIR-KABONGO ou KABONGO)",
            )
            password_input = forms.CharField(
                label="Mot de passe",
                widget=forms.PasswordInput,
                required=True,
            )

            class Meta:
                model = Directeur
                fields = ["titre", "nom", "postnom", "prenom"]

        if obj:
            kwargs["form"] = super().get_form(request, obj, **kwargs)
        else:
            kwargs["form"] = DirecteurForm
        return super().get_form(request, obj, **kwargs)

    def save_model(self, request, obj, form, change):
        if not change:
            identifiant = form.cleaned_data.get("identifiant_input", "").strip().upper()
            password = form.cleaned_data.get("password_input", "")
            if not identifiant:
                self.message_user(request, "L'identifiant est obligatoire.", messages.ERROR)
                return
            if User.objects.filter(identifiant=identifiant).exists():
                self.message_user(request, f"L'identifiant « {identifiant} » est déjà utilisé.", messages.ERROR)
                return
            user = User.objects.create_user(
                identifiant=identifiant,
                password=password,
                is_active=True,
                password_created=True,
            )
            obj.user = user
        super().save_model(request, obj, form, change)

    @admin.display(description="Nom / Identifiant")
    def nom_display(self, obj):
        parts = [p for p in [obj.prenom, obj.nom, obj.postnom] if p]
        return " ".join(parts) if parts else "—"

    @admin.display(description="Identifiant")
    def identifiant_display(self, obj):
        return obj.user.identifiant if obj.user_id else "—"

    @admin.display(description="Compte actif", boolean=True)
    def compte_actif(self, obj):
        return obj.user.is_active if obj.user_id else False


@admin.register(Professeur)
class ProfesseurAdmin(admin.ModelAdmin):
    list_display = ("nom_display", "identifiant_display", "compte_actif")
    search_fields = ("nom", "postnom", "prenom", "user__identifiant")
    autocomplete_fields = ()
    readonly_fields = ("compte_actif",)

    def get_fields(self, request, obj=None):
        if obj:
            return ("nom", "postnom", "prenom")
        return ("identifiant_input", "password_input", "nom", "postnom", "prenom")

    def get_form(self, request, obj=None, **kwargs):
        from django import forms

        class ProfesseurForm(forms.ModelForm):
            identifiant_input = forms.CharField(
                label="Identifiant de connexion",
                required=True,
                help_text="Identifiant unique pour se connecter (ex : PROF-KABONGO ou KABONGO)",
            )
            password_input = forms.CharField(
                label="Mot de passe",
                widget=forms.PasswordInput,
                required=True,
            )

            class Meta:
                model = Professeur
                fields = ["nom", "postnom", "prenom"]

        if obj:
            kwargs["form"] = super().get_form(request, obj, **kwargs)
        else:
            kwargs["form"] = ProfesseurForm
        return super().get_form(request, obj, **kwargs)

    def save_model(self, request, obj, form, change):
        if not change:
            identifiant = form.cleaned_data.get("identifiant_input", "").strip().upper()
            password = form.cleaned_data.get("password_input", "")
            if not identifiant:
                self.message_user(request, "L'identifiant est obligatoire.", messages.ERROR)
                return
            if User.objects.filter(identifiant=identifiant).exists():
                self.message_user(request, f"L'identifiant « {identifiant} » est déjà utilisé.", messages.ERROR)
                return
            user = User.objects.create_user(
                identifiant=identifiant,
                password=password,
                is_active=True,
                password_created=True,
            )
            obj.user = user
        super().save_model(request, obj, form, change)

    @admin.display(description="Nom / Identifiant")
    def nom_display(self, obj):
        parts = [p for p in [obj.prenom, obj.nom, obj.postnom] if p]
        return " ".join(parts) if parts else "—"

    @admin.display(description="Identifiant")
    def identifiant_display(self, obj):
        return obj.user.identifiant if obj.user_id else "—"

    @admin.display(description="Compte actif", boolean=True)
    def compte_actif(self, obj):
        return obj.user.is_active if obj.user_id else False


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
