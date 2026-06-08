from django.contrib.auth import login
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View

from accounts.forms import ProfesseurSignInForm
from accounts.models import Eleve, Professeur
from dashboard.models import Cours, EvaluationCours, Note
from professeur.forms import NoteForm


def professeur_required_dispatch(cls):
    original_dispatch = cls.dispatch

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(f"/professeur/connexion/?next={request.path}")
        try:
            _ = request.user.professeur
        except Exception:
            return redirect(f"/professeur/connexion/?next={request.path}")
        return original_dispatch(self, request, *args, **kwargs)

    cls.dispatch = dispatch
    return cls


class ProfesseurLoginView(View):
    template_name = "professeur/login.html"

    def get(self, request):
        try:
            if request.user.is_authenticated and request.user.professeur:
                return redirect("/professeur/")
        except Exception:
            pass
        form = ProfesseurSignInForm(request)
        return render(request, self.template_name, {"form": form})

    def post(self, request):
        form = ProfesseurSignInForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            try:
                _ = user.professeur
            except Exception:
                return render(request, self.template_name, {
                    "form": form,
                    "error": "Ce compte n'a pas accès à l'espace professeur.",
                })
            login(request, user)
            next_url = request.GET.get("next", "/professeur/")
            return redirect(next_url)
        return render(request, self.template_name, {"form": form})


@professeur_required_dispatch
class DashboardProfesseurView(View):
    template_name = "professeur/dashboard.html"

    def get(self, request):
        professeur = request.user.professeur
        cours = Cours.objects.filter(professeur=professeur).select_related("classe")
        classes = {c.classe for c in cours if c.classe is not None}
        eleves = Eleve.objects.filter(classe__in=[c for c in classes])
        notes_count = Note.objects.filter(evaluation_cours__cours__in=cours).count()

        context = {
            "professeur": professeur,
            "cours": cours,
            "classes": classes,
            "eleves_count": eleves.count(),
            "notes_count": notes_count,
        }
        return render(request, self.template_name, context)


@professeur_required_dispatch
class CoursProfesseurView(View):
    template_name = "professeur/cours.html"

    def get(self, request):
        professeur = request.user.professeur
        cours = Cours.objects.filter(professeur=professeur).select_related("classe")
        context = {"professeur": professeur, "cours": cours}
        return render(request, self.template_name, context)


@professeur_required_dispatch
class ClassesProfesseurView(View):
    template_name = "professeur/classes.html"

    def get(self, request):
        professeur = request.user.professeur
        cours = Cours.objects.filter(professeur=professeur).select_related("classe")
        classes = {c.classe for c in cours if c.classe is not None}
        context = {"professeur": professeur, "classes": classes}
        return render(request, self.template_name, context)


@professeur_required_dispatch
class ElevesProfesseurView(View):
    template_name = "professeur/eleves.html"

    def get(self, request):
        professeur = request.user.professeur
        classes = Cours.objects.filter(professeur=professeur).values_list("classe", flat=True)
        eleves = Eleve.objects.filter(classe__in=classes).select_related("classe", "user").order_by("classe__niveau", "nom")
        context = {"professeur": professeur, "eleves": eleves}
        return render(request, self.template_name, context)


@professeur_required_dispatch
class CoursNotesView(View):
    template_name = "professeur/notes.html"

    def get(self, request, cours_pk):
        professeur = request.user.professeur
        cours = get_object_or_404(Cours, pk=cours_pk, professeur=professeur)
        evaluations = EvaluationCours.objects.filter(cours=cours).select_related("evaluation")
        eleves = Eleve.objects.filter(classe=cours.classe).select_related("user").order_by("nom")
        notes = Note.objects.filter(evaluation_cours__in=evaluations, eleve__in=eleves).select_related(
            "eleve", "evaluation_cours__evaluation"
        )
        notes_by_eleve = {note.eleve_id: note for note in notes}
        eleve_rows = [
            {
                "eleve": eleve,
                "note": notes_by_eleve.get(eleve.id),
            }
            for eleve in eleves
        ]
        context = {
            "professeur": professeur,
            "cours": cours,
            "evaluations": evaluations,
            "eleve_rows": eleve_rows,
        }
        return render(request, self.template_name, context)


@professeur_required_dispatch
class NoteEditView(View):
    template_name = "professeur/note_form.html"

    def get(self, request, pk):
        note = get_object_or_404(Note, pk=pk, evaluation_cours__cours__professeur=request.user.professeur)
        form = NoteForm(instance=note, note_max=note.evaluation_cours.note_max)
        return render(request, self.template_name, {"note": note, "form": form})

    def post(self, request, pk):
        note = get_object_or_404(Note, pk=pk, evaluation_cours__cours__professeur=request.user.professeur)
        form = NoteForm(request.POST, instance=note, note_max=note.evaluation_cours.note_max)
        if form.is_valid():
            form.save()
            return redirect("professeur:cours_notes", cours_pk=note.evaluation_cours.cours_id)
        return render(request, self.template_name, {"note": note, "form": form})
