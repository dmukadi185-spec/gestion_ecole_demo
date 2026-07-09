from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError

from accounts.models import Eleve


class Cours(models.Model):
    nom = models.CharField(max_length=150)
    professeur = models.ForeignKey(
        "accounts.Professeur",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="cours",
    )
    classe = models.ForeignKey(
        "accounts.Classe",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="cours",
    )

    class Meta:
        verbose_name = "cours"
        verbose_name_plural = "cours"

    def __str__(self):
        return self.nom


class Evaluation(models.Model):
    TYPE_CHOICES = [
        ("interrogation", "Interrogation"),
        ("examen", "Examen"),
    ]
    PERIODE_CHOICES = [
        ("1p", "1ère période"),
        ("2p", "2ème période"),
        ("3p", "3ème période"),
        ("4p", "4ème période"),
        ("exam1", "Examen 1er semestre"),
        ("exam2", "Examen 2ème semestre"),
    ]
    SEMESTRE_CHOICES = [
        ("1", "1er semestre"),
        ("2", "2ème semestre"),
    ]

    nom = models.CharField(max_length=150, blank=True)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default="interrogation")
    periode = models.CharField(max_length=15, choices=PERIODE_CHOICES, default="1p")
    semestre = models.CharField(max_length=1, choices=SEMESTRE_CHOICES, editable=False)

    class Meta:
        verbose_name = "évaluation"
        verbose_name_plural = "évaluations"

    def save(self, *args, **kwargs):
        self.semestre = "1" if self.periode in {"1p", "2p", "exam1"} else "2"
        if not self.nom:
            self.nom = f"{self.get_type_display()} - {self.get_periode_display()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.get_type_display()} - {self.get_periode_display()}"


class EvaluationCours(models.Model):
    """Configuration de chaque type d'évaluation pour un cours spécifique"""
    cours = models.ForeignKey(Cours, on_delete=models.CASCADE, related_name="evaluations_config")
    evaluation = models.ForeignKey(Evaluation, on_delete=models.CASCADE, related_name="cours_config")
    note_max = models.DecimalField(max_digits=5, decimal_places=0, default=20, validators=[MinValueValidator(1)])
    ponderation = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=100,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Pondération en pourcentage (ex: 30 pour 30%)"
    )

    class Meta:
        verbose_name = "configuration évaluation-cours"
        verbose_name_plural = "configurations évaluation-cours"
        unique_together = ("cours", "evaluation")

    def __str__(self):
        return f"{self.cours} - {self.evaluation} (/{self.note_max}, {self.ponderation}%)"


class Note(models.Model):
    eleve = models.ForeignKey(Eleve, on_delete=models.CASCADE, related_name="notes")
    evaluation_cours = models.ForeignKey(EvaluationCours, on_delete=models.CASCADE, related_name="notes")
    valeur = models.DecimalField(max_digits=5, decimal_places=1)

    class Meta:
        verbose_name = "note"
        verbose_name_plural = "notes"
        unique_together = ("eleve", "evaluation_cours")

    def __str__(self):
        return f"{self.eleve} - {self.evaluation_cours}: {self.valeur}/{self.evaluation_cours.note_max}"

    def clean(self):
        """Ensure the note value does not exceed the configured maximum for the evaluation."""
        super().clean()
        if self.evaluation_cours and self.valeur is not None:
            try:
                max_val = self.evaluation_cours.note_max
                # Compare numerically using Decimal
                from decimal import Decimal

                if Decimal(str(self.valeur)) > Decimal(str(max_val)):
                    raise ValidationError({
                        "valeur": f"La valeur ne peut pas dépasser la note maximale ({max_val})."
                    })
            except Exception:
                # If conversion fails, let other validations raise appropriate errors
                pass

    def save(self, *args, **kwargs):
        # Enforce validation before saving to database
        self.full_clean()
        super().save(*args, **kwargs)

    @property
    def cours(self):
        return self.evaluation_cours.cours

    @property
    def evaluation(self):
        return self.evaluation_cours.evaluation
