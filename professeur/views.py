from django.contrib import messages
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
                return render(
                    request,
                    self.template_name,
                    {"form": form, "error": "Ce compte n'a pas accès à l'espace professeur."},
                )
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
        eleves = Eleve.objects.filter(classe__in=classes).select_related("classe", "user").order_by(
            "classe__niveau", "nom"
        )
        context = {"professeur": professeur, "eleves": eleves}
        return render(request, self.template_name, context)


@professeur_required_dispatch
class CoursNotesView(View):
    """Show all evaluations for a course with full note CRUD per student."""
    template_name = "professeur/notes.html"

    def get(self, request, cours_pk):
        professeur = request.user.professeur
        cours = get_object_or_404(Cours, pk=cours_pk, professeur=professeur)
        evaluations = EvaluationCours.objects.filter(cours=cours).select_related("evaluation").order_by(
            "evaluation__periode"
        )
        eleves = Eleve.objects.filter(classe=cours.classe).select_related("user").order_by("nom")

        evaluations_data = []
        for eval_cours in evaluations:
            eval_notes = {
                n.eleve_id: n
                for n in Note.objects.filter(evaluation_cours=eval_cours)
            }
            rows = [{"eleve": e, "note": eval_notes.get(e.id)} for e in eleves]
            evaluations_data.append({"evaluation_cours": eval_cours, "rows": rows})

        context = {
            "professeur": professeur,
            "cours": cours,
            "evaluations_data": evaluations_data,
            "eleves": eleves,
        }
        return render(request, self.template_name, context)


@professeur_required_dispatch
class NoteAddView(View):
    """Add a new note for a student in a specific evaluation of a course."""
    template_name = "professeur/note_form.html"

    def _get_context(self, eval_cours_pk, eleve_pk, professeur):
        eval_cours = get_object_or_404(
            EvaluationCours,
            pk=eval_cours_pk,
            cours__professeur=professeur,
        )
        eleve = get_object_or_404(Eleve, pk=eleve_pk, classe=eval_cours.cours.classe)
        if Note.objects.filter(evaluation_cours=eval_cours, eleve=eleve).exists():
            return None, None, None
        return eval_cours, eleve, None

    def get(self, request, eval_cours_pk, eleve_pk):
        professeur = request.user.professeur
        eval_cours = get_object_or_404(
            EvaluationCours, pk=eval_cours_pk, cours__professeur=professeur
        )
        eleve = get_object_or_404(Eleve, pk=eleve_pk, classe=eval_cours.cours.classe)
        if Note.objects.filter(evaluation_cours=eval_cours, eleve=eleve).exists():
            messages.warning(request, "Une note existe déjà pour cet élève.")
            return redirect("professeur:cours_notes", cours_pk=eval_cours.cours_id)
        form = NoteForm(note_max=eval_cours.note_max)
        return render(request, self.template_name, {
            "form": form,
            "eval_cours": eval_cours,
            "eleve": eleve,
            "mode": "add",
        })

    def post(self, request, eval_cours_pk, eleve_pk):
        professeur = request.user.professeur
        eval_cours = get_object_or_404(
            EvaluationCours, pk=eval_cours_pk, cours__professeur=professeur
        )
        eleve = get_object_or_404(Eleve, pk=eleve_pk, classe=eval_cours.cours.classe)
        if Note.objects.filter(evaluation_cours=eval_cours, eleve=eleve).exists():
            messages.warning(request, "Une note existe déjà pour cet élève.")
            return redirect("professeur:cours_notes", cours_pk=eval_cours.cours_id)
        form = NoteForm(request.POST, note_max=eval_cours.note_max)
        if form.is_valid():
            note = form.save(commit=False)
            note.evaluation_cours = eval_cours
            note.eleve = eleve
            note.save()
            messages.success(request, f"Note ajoutée pour {eleve.nom_complet}.")
            return redirect("professeur:cours_notes", cours_pk=eval_cours.cours_id)
        return render(request, self.template_name, {
            "form": form,
            "eval_cours": eval_cours,
            "eleve": eleve,
            "mode": "add",
        })


@professeur_required_dispatch
class NoteEditView(View):
    template_name = "professeur/note_form.html"

    def get(self, request, pk):
        note = get_object_or_404(
            Note, pk=pk, evaluation_cours__cours__professeur=request.user.professeur
        )
        form = NoteForm(instance=note, note_max=note.evaluation_cours.note_max)
        return render(request, self.template_name, {
            "form": form,
            "note": note,
            "eval_cours": note.evaluation_cours,
            "eleve": note.eleve,
            "mode": "edit",
        })

    def post(self, request, pk):
        note = get_object_or_404(
            Note, pk=pk, evaluation_cours__cours__professeur=request.user.professeur
        )
        form = NoteForm(request.POST, instance=note, note_max=note.evaluation_cours.note_max)
        if form.is_valid():
            form.save()
            messages.success(request, f"Note modifiée pour {note.eleve.nom_complet}.")
            return redirect("professeur:cours_notes", cours_pk=note.evaluation_cours.cours_id)
        return render(request, self.template_name, {
            "form": form,
            "note": note,
            "eval_cours": note.evaluation_cours,
            "eleve": note.eleve,
            "mode": "edit",
        })


@professeur_required_dispatch
class NoteDeleteView(View):
    def post(self, request, pk):
        note = get_object_or_404(
            Note, pk=pk, evaluation_cours__cours__professeur=request.user.professeur
        )
        cours_pk = note.evaluation_cours.cours_id
        nom_eleve = note.eleve.nom_complet
        note.delete()
        messages.success(request, f"Note de {nom_eleve} supprimée.")
        return redirect("professeur:cours_notes", cours_pk=cours_pk)
