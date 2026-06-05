from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.core.exceptions import ValidationError
from django.db import models


class UserManager(BaseUserManager):
    def create_user(self, identifiant, password=None, **extra_fields):
        if not identifiant:
            raise ValueError("L'identifiant est obligatoire.")
        identifiant = " ".join(identifiant.strip().split()).upper()
        user = self.model(identifiant=identifiant, **extra_fields)
        if password:
            user.set_password(password)
            user.password_created = True
        else:
            user.set_unusable_password()
            user.password_created = False
        user.save(using=self._db)
        return user

    def create_superuser(self, identifiant, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("password_created", True)
        if extra_fields.get("is_staff") is not True:
            raise ValueError("Le superutilisateur doit avoir is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Le superutilisateur doit avoir is_superuser=True.")
        return self.create_user(identifiant, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    identifiant = models.CharField(max_length=50, unique=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    password_created = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = "identifiant"
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = "utilisateur"
        verbose_name_plural = "utilisateurs"

    def __str__(self):
        return self.identifiant

    def save(self, *args, **kwargs):
        if self.identifiant:
            self.identifiant = " ".join(self.identifiant.strip().split()).upper()
        super().save(*args, **kwargs)


class Classe(models.Model):
    niveau = models.CharField(max_length=100)
    departement = models.CharField(max_length=100)

    class Meta:
        verbose_name = "classe"
        verbose_name_plural = "classes"

    def __str__(self):
        return f"{self.niveau} - {self.departement}"


class Directeur(models.Model):
    TITRE_CHOICES = [
        ("directeur_general", "Directeur Général"),
        ("directeur_adjoint", "Directeur Adjoint"),
        ("censeur", "Censeur"),
        ("prefet", "Préfet des études"),
        ("autre", "Autre"),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="directeur")
    nom = models.CharField(max_length=100, blank=True)
    postnom = models.CharField(max_length=100, blank=True)
    prenom = models.CharField(max_length=100, blank=True)
    titre = models.CharField(max_length=30, choices=TITRE_CHOICES, default="directeur_general")

    class Meta:
        verbose_name = "directeur"
        verbose_name_plural = "directeurs"

    def __str__(self):
        parts = [p for p in [self.prenom, self.nom, self.postnom] if p]
        name = " ".join(parts) if parts else self.user.identifiant
        return f"{self.get_titre_display()} — {name}"

    @property
    def nom_complet(self):
        parts = [p for p in [self.prenom, self.nom, self.postnom] if p]
        return " ".join(parts) if parts else self.user.identifiant

    @property
    def is_directeur(self):
        return True


class Eleve(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="eleve")
    nom = models.CharField(max_length=100)
    postnom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    classe = models.ForeignKey(Classe, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        verbose_name = "élève"
        verbose_name_plural = "élèves"

    def __str__(self):
        return f"{self.prenom} {self.nom} {self.postnom}"

    @property
    def nom_complet(self):
        return f"{self.prenom} {self.nom} {self.postnom}"

    @staticmethod
    def generate_identifiant(nom, postnom, prenom):
        """Identifiant = NOM POSTNOM PRENOM, séparés par des espaces, en majuscules."""
        parts = [nom.strip(), postnom.strip(), prenom.strip()]
        return " ".join(" ".join(parts).split()).upper()

    def get_identifiant(self):
        return self.generate_identifiant(self.nom, self.postnom, self.prenom)

    def sync_user_identifiant(self):
        """Met à jour l'identifiant du compte lié ; lève ValidationError si doublon."""
        new_identifiant = self.get_identifiant()
        if self.user.identifiant == new_identifiant:
            return
        if User.objects.filter(identifiant=new_identifiant).exclude(pk=self.user_id).exists():
            raise ValidationError(
                f"L'identifiant « {new_identifiant} » existe déjà pour un autre élève."
            )
        self.user.identifiant = new_identifiant
        self.user.save(update_fields=["identifiant"])
