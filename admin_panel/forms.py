from django import forms

from accounts.models import Eleve, Professeur, User
from dashboard.models import Cours


class EleveForm(forms.ModelForm):
    class Meta:
        model = Eleve
        fields = ["nom", "postnom", "prenom", "classe"]
        widgets = {
            "nom": forms.TextInput(attrs={"class": "form-control", "style": "text-transform:uppercase"}),
            "postnom": forms.TextInput(attrs={"class": "form-control", "style": "text-transform:uppercase"}),
            "prenom": forms.TextInput(attrs={"class": "form-control", "style": "text-transform:uppercase"}),
            "classe": forms.Select(attrs={"class": "form-select"}),
        }

    def clean_nom(self):
        return self.cleaned_data["nom"].strip().upper()

    def clean_postnom(self):
        return self.cleaned_data["postnom"].strip().upper()

    def clean_prenom(self):
        return self.cleaned_data["prenom"].strip().upper()

    def validate_identifiant_unique(self, exclude_user_pk=None):
        nom = self.cleaned_data.get("nom", "")
        postnom = self.cleaned_data.get("postnom", "")
        prenom = self.cleaned_data.get("prenom", "")
        if nom and postnom and prenom:
            identifiant = Eleve.generate_identifiant(nom, postnom, prenom)
            qs = User.objects.filter(identifiant=identifiant)
            if exclude_user_pk:
                qs = qs.exclude(pk=exclude_user_pk)
            if qs.exists():
                raise forms.ValidationError(
                    f"L'identifiant « {identifiant} » est déjà utilisé par un autre compte."
                )

    def save_with_user(self, existing_eleve=None):
        """Create or update an Eleve along with its User account."""
        nom = self.cleaned_data["nom"]
        postnom = self.cleaned_data["postnom"]
        prenom = self.cleaned_data["prenom"]
        classe = self.cleaned_data["classe"]
        identifiant = Eleve.generate_identifiant(nom, postnom, prenom)

        if existing_eleve:
            self.validate_identifiant_unique(exclude_user_pk=existing_eleve.user_id)
            existing_eleve.nom = nom
            existing_eleve.postnom = postnom
            existing_eleve.prenom = prenom
            existing_eleve.classe = classe
            existing_eleve.save()
            existing_eleve.user.identifiant = identifiant
            existing_eleve.user.save(update_fields=["identifiant"])
            return existing_eleve
        else:
            self.validate_identifiant_unique()
            user = User.objects.create_user(identifiant=identifiant)
            eleve = Eleve.objects.create(
                user=user,
                nom=nom,
                postnom=postnom,
                prenom=prenom,
                classe=classe,
            )
            return eleve


class ProfesseurCreateForm(forms.Form):
    nom = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={"class": "form-control", "style": "text-transform:uppercase"}),
    )
    postnom = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "style": "text-transform:uppercase"}),
    )
    prenom = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "style": "text-transform:uppercase"}),
    )
    identifiant = forms.CharField(
        max_length=50,
        label="Identifiant de connexion",
        help_text="Identifiant unique utilisé pour se connecter (ex: DUPONT JEAN).",
        widget=forms.TextInput(
            attrs={"class": "form-control", "style": "text-transform:uppercase"}
        ),
    )
    password = forms.CharField(
        label="Mot de passe",
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
    )
    password_confirm = forms.CharField(
        label="Confirmer le mot de passe",
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
    )

    def clean_nom(self):
        return self.cleaned_data["nom"].strip().upper()

    def clean_postnom(self):
        return self.cleaned_data.get("postnom", "").strip().upper()

    def clean_prenom(self):
        return self.cleaned_data.get("prenom", "").strip().upper()

    def clean_identifiant(self):
        val = " ".join(self.cleaned_data["identifiant"].strip().split()).upper()
        if User.objects.filter(identifiant=val).exists():
            raise forms.ValidationError("Cet identifiant est déjà utilisé.")
        return val

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get("password")
        p2 = cleaned.get("password_confirm")
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError("Les mots de passe ne correspondent pas.")
        return cleaned

    def save(self):
        data = self.cleaned_data
        user = User.objects.create_user(
            identifiant=data["identifiant"],
            password=data["password"],
        )
        prof = Professeur.objects.create(
            user=user,
            nom=data["nom"],
            postnom=data.get("postnom", ""),
            prenom=data.get("prenom", ""),
        )
        return prof


class ProfesseurEditForm(forms.ModelForm):
    class Meta:
        model = Professeur
        fields = ["nom", "postnom", "prenom"]
        widgets = {
            "nom": forms.TextInput(attrs={"class": "form-control", "style": "text-transform:uppercase"}),
            "postnom": forms.TextInput(attrs={"class": "form-control", "style": "text-transform:uppercase"}),
            "prenom": forms.TextInput(attrs={"class": "form-control", "style": "text-transform:uppercase"}),
        }

    def clean_nom(self):
        return self.cleaned_data["nom"].strip().upper()

    def clean_postnom(self):
        return self.cleaned_data.get("postnom", "").strip().upper()

    def clean_prenom(self):
        return self.cleaned_data.get("prenom", "").strip().upper()


class CoursForm(forms.ModelForm):
    class Meta:
        model = Cours
        fields = ["nom", "professeur", "classe"]
        widgets = {
            "nom": forms.TextInput(attrs={"class": "form-control"}),
            "professeur": forms.Select(attrs={"class": "form-select"}),
            "classe": forms.Select(attrs={"class": "form-select"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["professeur"].required = True
        self.fields["classe"].required = True
        self.fields["professeur"].empty_label = "— Choisir un professeur —"
        self.fields["classe"].empty_label = "— Choisir une classe —"
