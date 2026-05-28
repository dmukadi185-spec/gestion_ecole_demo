from django.contrib import admin

from .models import FraisScolaire, Paiement


@admin.register(FraisScolaire)
class FraisScolaireAdmin(admin.ModelAdmin):
    list_display = ("type_frais", "mois", "montant")
    list_filter = ("type_frais", "mois")
    search_fields = ("type_frais", "mois")


@admin.register(Paiement)
class PaiementAdmin(admin.ModelAdmin):
    list_display = (
        "numero_transaction",
        "eleve",
        "frais",
        "moyen_paiement",
        "montant",
        "date_paiement",
        "statut",
    )
    list_filter = ("statut", "date_paiement", "moyen_paiement")
    search_fields = ("numero_transaction", "eleve__nom", "eleve__prenom")
    autocomplete_fields = ("eleve", "frais")
