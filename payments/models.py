from django.db import models
from django.utils import timezone

from accounts.models import Eleve


class FraisScolaire(models.Model):
    TYPE_CHOICES = [
        ("minerval", "Minerval"),
        ("autre", "Autre"),
    ]

    MOIS_CHOICES = [
        ("septembre", "Septembre"),
        ("octobre", "Octobre"),
        ("novembre", "Novembre"),
        ("decembre", "Décembre"),
        ("janvier", "Janvier"),
        ("fevrier", "Février"),
        ("mars", "Mars"),
        ("avril", "Avril"),
        ("mai", "Mai"),
        ("juin", "Juin"),
    ]

    type_frais = models.CharField(max_length=20, choices=TYPE_CHOICES, default="minerval")
    mois = models.CharField(max_length=15, choices=MOIS_CHOICES)
    montant = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        verbose_name = "frais scolaire"
        verbose_name_plural = "frais scolaires"
        unique_together = ("type_frais", "mois")

    def __str__(self):
        return f"{self.get_type_frais_display()} {self.get_mois_display()}"


class Paiement(models.Model):
    MODE_CHOICES = [
        ("orange", "Orange Money"),
        ("airtel", "Airtel Money"),
        ("mpesa", "M-Pesa"),
    ]

    STATUT_CHOICES = [
        ("en_attente", "En attente"),
        ("paye", "Payé"),
        ("echec", "Échec"),
    ]

    eleve = models.ForeignKey(Eleve, on_delete=models.CASCADE, related_name="paiements")
    frais = models.ForeignKey(FraisScolaire, null=True, blank=True, on_delete=models.PROTECT, related_name="paiements")
    moyen_paiement = models.CharField(max_length=20, choices=MODE_CHOICES, null=True, blank=True)
    montant = models.DecimalField(max_digits=10, decimal_places=2, editable=False, null=True, blank=True)
    description = models.CharField(max_length=255, blank=True)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default="paye")
    date_paiement = models.DateTimeField(auto_now_add=True)
    numero_transaction = models.CharField(max_length=100, unique=True, blank=True)

    class Meta:
        verbose_name = "paiement"
        verbose_name_plural = "paiements"
        ordering = ["-date_paiement"]
        unique_together = ("eleve", "frais")

    def save(self, *args, **kwargs):
        if self.frais_id and not self.montant:
            self.montant = self.frais.montant
        if self.frais_id and not self.description:
            self.description = f"{self.frais.get_type_frais_display()} mois de {self.frais.get_mois_display()}"
        if not self.numero_transaction:
            self.numero_transaction = timezone.now().strftime("PMT%Y%m%d%H%M%S%f")
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.numero_transaction} - {self.montant}"
