from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from accounts.utils import get_eleve_for_user, render_no_eleve_profile
from .forms import PaiementForm
from .models import FraisScolaire, Paiement

MONTH_ORDER = [
    "septembre",
    "octobre",
    "novembre",
    "decembre",
    "janvier",
    "fevrier",
    "mars",
    "avril",
    "mai",
    "juin",
]


def _ordered_frais(queryset):
    return sorted(queryset, key=lambda frais: MONTH_ORDER.index(frais.mois))


@login_required(login_url="accounts:signin")
def liste_paiements(request):
    eleve = get_eleve_for_user(request.user)
    if eleve is None:
        return render_no_eleve_profile(request)

    frais_list = _ordered_frais(FraisScolaire.objects.filter(type_frais="minerval"))
    paiements = Paiement.objects.filter(eleve=eleve, statut="paye").select_related("frais")
    paye_frais_ids = {paiement.frais_id for paiement in paiements}
    mois_status = []
    for frais in frais_list:
        mois_status.append(
            {
                "frais": frais,
                "statut": "Payé" if frais.id in paye_frais_ids else "Non payé",
            }
        )

    prochain_frais = next((f for f in frais_list if f.id not in paye_frais_ids), None)

    return render(
        request,
        "payments/paiements.html",
        {
            "eleve": eleve,
            "paiements": paiements,
            "mois_status": mois_status,
            "prochain_frais": prochain_frais,
        },
    )


@login_required(login_url="accounts:signin")
def effectuer_paiement(request):
    eleve = get_eleve_for_user(request.user)
    if eleve is None:
        return render_no_eleve_profile(request)

    frais_list = _ordered_frais(FraisScolaire.objects.filter(type_frais="minerval"))
    paiements = Paiement.objects.filter(eleve=eleve, statut="paye").values_list("frais_id", flat=True)
    prochain_frais = next((f for f in frais_list if f.id not in paiements), None)

    if prochain_frais is None:
        return render(
            request,
            "payments/effectuer_paiement.html",
            {
                "eleve": eleve,
                "message": "Tous les mois autorisés ont déjà été payés.",
                "prochain_frais": None,
            },
        )

    if request.method == "POST":
        form = PaiementForm(request.POST, allowed_frais=FraisScolaire.objects.filter(pk=prochain_frais.pk))
        if form.is_valid():
            paiement = form.save(commit=False)
            paiement.eleve = eleve
            paiement.montant = paiement.frais.montant
            paiement.description = f"{paiement.frais.get_type_frais_display()} mois de {paiement.frais.get_mois_display()}"
            paiement.statut = "paye"
            paiement.save()
            return redirect("payments:liste")
    else:
        form = PaiementForm(allowed_frais=FraisScolaire.objects.filter(pk=prochain_frais.pk))

    return render(
        request,
        "payments/effectuer_paiement.html",
        {
            "eleve": eleve,
            "form": form,
            "prochain_frais": prochain_frais,
        },
    )


@login_required(login_url="accounts:signin")
def recu(request, pk):
    eleve = get_eleve_for_user(request.user)
    if eleve is None:
        return render_no_eleve_profile(request)
    paiement = get_object_or_404(Paiement, pk=pk, eleve=eleve)
    return render(
        request,
        "payments/recu.html",
        {"eleve": eleve, "paiement": paiement},
    )
