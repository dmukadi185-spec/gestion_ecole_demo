from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render

from accounts.utils import get_eleve_for_user, render_no_eleve_profile
from dashboard.models import Cours, Evaluation, EvaluationCours, Note
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

    cours_list = Cours.objects.filter(classe=eleve.classe).order_by("nom") if eleve.classe else Cours.objects.none()
    cours_id = request.GET.get("cours")
    selected_course = None
    if cours_id:
        selected_course = get_object_or_404(Cours, pk=cours_id, classe=eleve.classe)

    periode_order = [choice[0] for choice in Evaluation.PERIODE_CHOICES]
    periode_labels = dict(Evaluation.PERIODE_CHOICES)
    periode_headers = [periode_labels[periode] for periode in periode_order]

    evaluation_cours_qs = (
        EvaluationCours.objects.filter(cours__classe=eleve.classe)
        .select_related("cours", "evaluation")
        .order_by("cours__nom", "evaluation__periode")
    )
    note_qs = (
        Note.objects.filter(eleve=eleve)
        .select_related("evaluation_cours__evaluation", "evaluation_cours__cours")
    )

    evaluation_map = {
        (eval_cours.cours_id, eval_cours.evaluation.periode): eval_cours
        for eval_cours in evaluation_cours_qs
    }
    note_map = {
        (note_obj.evaluation_cours.cours_id, note_obj.evaluation_cours.evaluation.periode): note_obj
        for note_obj in note_qs
    }

    rows = []
    for cours in cours_list:
        if selected_course and cours.pk != selected_course.pk:
            continue
        cells = []
        for periode in periode_order:
            cells.append({
                "periode": periode,
                "evaluation_cours": evaluation_map.get((cours.pk, periode)),
                "note": note_map.get((cours.pk, periode)),
            })
        rows.append({"cours": cours, "cells": cells})

    context = {
        "eleve": eleve,
        "cours_list": cours_list,
        "cours_selectionne": selected_course,
        "rows": rows,
        "periode_labels": periode_labels,
        "periode_headers": periode_headers,
        "periode_order": periode_order,
    }
    return render(request, "dashboard/resultats.html", context)
