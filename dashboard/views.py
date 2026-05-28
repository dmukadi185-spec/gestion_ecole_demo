from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render

from accounts.utils import get_eleve_for_user, render_no_eleve_profile
from dashboard.models import Cours, EvaluationCours, Note
from payments.models import Paiement


@login_required(login_url="accounts:signin")
def index(request):
    eleve = get_eleve_for_user(request.user)
    if eleve is None:
        return render_no_eleve_profile(request)
    notes_recentes = Note.objects.filter(eleve=eleve).select_related("evaluation_cours__evaluation")[:5]
    paiements_recents = Paiement.objects.filter(eleve=eleve)[:5]
    context = {
        "eleve": eleve,
        "notes_recentes": notes_recentes,
        "paiements_recents": paiements_recents,
    }
    return render(request, "dashboard/dashboard.html", context)


@login_required(login_url="accounts:signin")
def resultats(request):
    eleve = get_eleve_for_user(request.user)
    if eleve is None:
        return render_no_eleve_profile(request)
    cours_list = Cours.objects.all().order_by("nom")

    cours_id = request.GET.get("cours")
    evaluation_id = request.GET.get("evaluation")
    note = None
    cours_selectionne = None
    evaluation_selectionnee = None
    evaluations = EvaluationCours.objects.none()

    if cours_id:
        cours_selectionne = get_object_or_404(Cours, pk=cours_id)
        evaluations = (
            EvaluationCours.objects.filter(cours=cours_selectionne)
            .select_related("evaluation")
            .order_by("evaluation__periode")
        )

    if evaluation_id:
        evaluation_selectionnee = get_object_or_404(EvaluationCours, pk=evaluation_id)
        note = (
            Note.objects.filter(
                eleve=eleve,
                evaluation_cours=evaluation_selectionnee,
            )
            .first()
        )

    context = {
        "eleve": eleve,
        "cours_list": cours_list,
        "evaluations": evaluations,
        "cours_selectionne": cours_selectionne,
        "evaluation_selectionnee": evaluation_selectionnee,
        "note": note,
    }
    return render(request, "dashboard/resultats.html", context)
