from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.forms import AuthenticationForm

from .models import Eleve, User
from .utils import normalize_identifiant

IDENTIFIANT_HELP = (
    "Votre identifiant est votre nom, postnom et prénom séparés par des espaces, "
    "en majuscules. Exemple : DUPONT MBUYA KABONGO"
)


class BaseAuthForm(AuthenticationForm):
    """Formulaire d'authentification de base — vérifie identifiant + mot de passe uniquement."""

    username = forms.CharField(
        label="Identifiant",
        max_length=50,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "autocomplete": "username",
                "placeholder": "NOM POSTNOM PRENOM",
                "style": "text-transform: uppercase",
            }
        ),
    )
    password = forms.CharField(
        label="Mot de passe",
        widget=forms.PasswordInput(attrs={"class": "form-control", "autocomplete": "current-password"}),
    )

    def clean_username(self):
        value = self.cleaned_data.get("username", "")
        return normalize_identifiant(value)

    def clean(self):
        identifiant = self.cleaned_data.get("username")
        password = self.cleaned_data.get("password")
        if identifiant and password:
            self.user_cache = authenticate(
                self.request, username=identifiant, password=password,
            )
            if self.user_cache is None:
                raise forms.ValidationError("Identifiant ou mot de passe incorrect.")
            if not self.user_cache.is_active:
                raise forms.ValidationError("Ce compte est désactivé.")
        return self.cleaned_data


class SignInForm(BaseAuthForm):
    """Formulaire pour les élèves — vérifie en plus qu'un profil élève existe."""

    username = forms.CharField(
        label="Identifiant scolaire",
        max_length=50,
        help_text=IDENTIFIANT_HELP,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "autocomplete": "username",
                "placeholder": "NOM POSTNOM PRENOM",
                "style": "text-transform: uppercase",
            }
        ),
    )

    def clean(self):
        super().clean()
        user = self.user_cache
        if user:
            if not user.password_created:
                raise forms.ValidationError(
                    "Vous devez d'abord créer votre mot de passe via « Créer mon mot de passe »."
                )
            if not user.is_staff and not hasattr(user, 'directeur'):
                if not Eleve.objects.filter(user=user).exists():
                    raise forms.ValidationError(
                        "Aucun profil élève associé à cet identifiant. "
                        "Contactez l'administration de l'école."
                    )
        return self.cleaned_data


class StaffSignInForm(BaseAuthForm):
    """Formulaire pour les admins staff — authentification simple sans vérification de rôle."""
    pass


class DirecteurSignInForm(BaseAuthForm):
    """Formulaire pour les directeurs — authentification simple sans vérification de rôle."""
    pass


class ProfesseurSignInForm(BaseAuthForm):
    """Formulaire pour les professeurs — authentification simple sans vérification de rôle."""
    pass


class ActivateAccountForm(forms.Form):
    identifiant = forms.CharField(
        label="Identifiant scolaire",
        max_length=50,
        help_text=IDENTIFIANT_HELP,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "NOM POSTNOM PRENOM",
                "style": "text-transform: uppercase",
            }
        ),
    )
    password = forms.CharField(
        label="Nouveau mot de passe",
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
    )
    password_confirm = forms.CharField(
        label="Confirmation du mot de passe",
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
    )

    def clean_identifiant(self):
        identifiant = normalize_identifiant(self.cleaned_data["identifiant"])
        try:
            user = User.objects.get(identifiant=identifiant)
        except User.DoesNotExist:
            raise forms.ValidationError(
                "Aucun compte trouvé pour cet identifiant. "
                "Vérifiez que vous êtes bien inscrit par l'administration."
            )
        if not Eleve.objects.filter(user=user).exists():
            raise forms.ValidationError(
                "Aucun profil élève associé à cet identifiant. "
                "Vous devez être inscrit par l'administration avant de créer votre mot de passe."
            )
        if user.password_created:
            raise forms.ValidationError("Ce compte possède déjà un mot de passe. Connectez-vous.")
        self.user = user
        return identifiant

    def clean(self):
        cleaned = super().clean()
        password = cleaned.get("password")
        password_confirm = cleaned.get("password_confirm")
        if password and password_confirm and password != password_confirm:
            raise forms.ValidationError("Les mots de passe ne correspondent pas.")
        return cleaned

    def save(self):
        user = self.user
        user.set_password(self.cleaned_data["password"])
        user.password_created = True
        user.is_active = True
        user.save()
        return user
