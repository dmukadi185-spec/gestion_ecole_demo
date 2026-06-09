from django.contrib import messages
from django.contrib.auth import login
from django.db import transaction
from django.db.models import Count, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View

from accounts.forms import DirecteurSignInForm
from accounts.models import Classe, Directeur, Eleve, Professeur, User
from dashboard.models import Cours, EvaluationCours, Note
from payments.models import FraisScolaire, Paiement

from .forms import CoursForm, EleveForm, ProfesseurCreateForm, ProfesseurEditForm


def directeur_required(view_func=None):
    def decorator(func):
        from functools import wraps

        @wraps(func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect(f"/administration/connexion/?next={request.path}")
            try:
                _ = request.user.directeur
            except Exception:
                return redirect(f"/administration/connexion/?next={request.path}")
            return func(request, *args, **kwargs)

        return wrapper

    return decorator if view_func is None else decorator(view_func)


def directeur_required_dispatch(cls):
    original_dispatch = cls.dispatch

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(f"/administration/connexion/?next={request.path}")
        try:
            _ = request.user.directeur
        except Exception:
            return redirect(f"/administration/connexion/?next={request.path}")
        return original_dispatch(self, request, *args, **kwargs)

    cls.dispatch = dispatch
    return cls


class AdminLoginView(View):
    template_name = "admin_panel/login.html"

    def get(self, request):
        try:
            if request.user.is_authenticated and request.user.directeur:
                return redirect("/administration/")
        except Exception:
            pass
        form = DirecteurSignInForm(request)
        return render(request, self.template_name, {"form": form})

    def post(self, request):
        form = DirecteurSignInForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            try:
                _ = user.directeur
            except Exception:
                return render(
                    request,
                    self.template_name,
                    {"form": form, "error": "Ce compte n'a pas accès à l'espace directeur."},
                )
            login(request, user)
            next_url = request.GET.get("next", "/administration/")
            return redirect(next_url)
        return render(request, self.template_name, {"form": form})


MOIS_ORDER = [
    "septembre", "octobre", "novembre", "decembre",
    "janvier", "fevrier", "mars", "avril", "mai", "juin",
]


@directeur_required_dispatch
class DashboardAdminView(View):
    template_name = "admin_panel/dashboard.html"

    def get(self, request):
        total_eleves = Eleve.objects.count()
        total_classes = Classe.objects.count()
        total_cours = Cours.objects.count()
        total_professeurs = Professeur.objects.count()

        paiements_qs = Paiement.objects.filter(statut="paye")
        total_encaisse = paiements_qs.aggregate(total=Sum("montant"))["total"] or 0

        total_en_attente_montant = (
            Paiement.objects.filter(statut="en_attente").aggregate(total=Sum("montant"))["total"] or 0
        )
        total_echec = Paiement.objects.filter(statut="echec").count()

        paiements_par_statut = (
            Paiement.objects.values("statut")
            .annotate(nombre=Count("id"), montant_total=Sum("montant"))
            .order_by("statut")
        )
        statut_labels = []
        statut_data = []
        for s in paiements_par_statut:
            statut_labels.append(dict(Paiement.STATUT_CHOICES).get(s["statut"], s["statut"]))
            statut_data.append(float(s["montant_total"] or 0))

        paiements_par_mois_qs = (
            Paiement.objects.filter(statut="paye")
            .values("frais__mois")
            .annotate(total=Sum("montant"), nombre=Count("id"))
        )
        mois_dict = {p["frais__mois"]: p for p in paiements_par_mois_qs}
        mois_labels = []
        mois_data = []
        mois_nombres = []
        for m in MOIS_ORDER:
            label = dict(FraisScolaire.MOIS_CHOICES).get(m, m.capitalize())
            mois_labels.append(label)
            mois_data.append(float(mois_dict.get(m, {}).get("total", 0)))
            mois_nombres.append(mois_dict.get(m, {}).get("nombre", 0))

        par_moyen = (
            Paiement.objects.filter(statut="paye")
            .values("moyen_paiement")
            .annotate(total=Sum("montant"), nombre=Count("id"))
        )
        moyen_labels = []
        moyen_data = []
        for p in par_moyen:
            label = dict(Paiement.MODE_CHOICES).get(p["moyen_paiement"], p["moyen_paiement"] or "N/A")
            moyen_labels.append(label)
            moyen_data.append(float(p["total"] or 0))

        classes = Classe.objects.prefetch_related("eleve_set").all()
        taux_par_classe = []
        for cls in classes:
            eleves_cls = cls.eleve_set.count()
            if eleves_cls == 0:
                continue
            payes = (
                Paiement.objects.filter(eleve__classe=cls, statut="paye")
                .values("eleve")
                .distinct()
                .count()
            )
            taux = round((payes / eleves_cls) * 100) if eleves_cls > 0 else 0
            taux_par_classe.append({"classe": str(cls), "eleves": eleves_cls, "payes": payes, "taux": taux})

        eleves_sans_paiement = Eleve.objects.filter(paiements__isnull=True).count()

        derniers_paiements = Paiement.objects.select_related(
            "eleve", "frais", "eleve__classe"
        ).order_by("-date_paiement")[:15]

        par_type_frais = (
            Paiement.objects.filter(statut="paye")
            .values("frais__type_frais")
            .annotate(total=Sum("montant"), nombre=Count("id"))
        )
        type_frais_data = []
        for t in par_type_frais:
            label = dict(FraisScolaire.TYPE_CHOICES).get(
                t["frais__type_frais"], t["frais__type_frais"] or "Autre"
            )
            type_frais_data.append({"label": label, "total": float(t["total"] or 0), "nombre": t["nombre"]})

        context = {
            "total_eleves": total_eleves,
            "total_classes": total_classes,
            "total_cours": total_cours,
            "total_professeurs": total_professeurs,
            "total_encaisse": total_encaisse,
            "total_en_attente_montant": total_en_attente_montant,
            "total_echec": total_echec,
            "statut_labels": statut_labels,
            "statut_data": statut_data,
            "mois_labels": mois_labels,
            "mois_data": mois_data,
            "mois_nombres": mois_nombres,
            "moyen_labels": moyen_labels,
            "moyen_data": moyen_data,
            "taux_par_classe": taux_par_classe,
            "eleves_sans_paiement": eleves_sans_paiement,
            "derniers_paiements": derniers_paiements,
            "type_frais_data": type_frais_data,
        }
        return render(request, self.template_name, context)


# ─── ÉLÈVES ────────────────────────────────────────────────────────────────────

@directeur_required_dispatch
class ElevesAdminView(View):
    template_name = "admin_panel/eleves.html"

    def get(self, request):
        classe_id = request.GET.get("classe")
        statut_filtre = request.GET.get("statut")

        eleves_qs = Eleve.objects.select_related("user", "classe").prefetch_related("paiements")
        if classe_id:
            eleves_qs = eleves_qs.filter(classe_id=classe_id)

        eleves_data = []
        for eleve in eleves_qs:
            nb_payes = eleve.paiements.filter(statut="paye").count()
            montant_paye = eleve.paiements.filter(statut="paye").aggregate(total=Sum("montant"))["total"] or 0
            eleves_data.append({
                "eleve": eleve,
                "nb_payes": nb_payes,
                "montant_paye": montant_paye,
                "compte_actif": eleve.user.is_active,
                "mdp_cree": eleve.user.password_created,
            })

        if statut_filtre == "avec_paiement":
            eleves_data = [e for e in eleves_data if e["nb_payes"] > 0]
        elif statut_filtre == "sans_paiement":
            eleves_data = [e for e in eleves_data if e["nb_payes"] == 0]

        classes = Classe.objects.all()
        context = {
            "eleves_data": eleves_data,
            "classes": classes,
            "classe_selectionnee": classe_id,
            "statut_filtre": statut_filtre,
        }
        return render(request, self.template_name, context)


@directeur_required_dispatch
class EleveCreateView(View):
    template_name = "admin_panel/eleve_form.html"

    def get(self, request):
        form = EleveForm()
        return render(request, self.template_name, {"form": form, "action": "Ajouter"})

    def post(self, request):
        form = EleveForm(request.POST)
        if form.is_valid():
            try:
                eleve = form.save_with_user()
                messages.success(
                    request,
                    f"Élève « {eleve.nom_complet} » ajouté avec succès. "
                    f"Identifiant de connexion : {eleve.user.identifiant}",
                )
                return redirect("admin_panel:eleves")
            except Exception as e:
                form.add_error(None, str(e))
        return render(request, self.template_name, {"form": form, "action": "Ajouter"})


@directeur_required_dispatch
class EleveEditView(View):
    template_name = "admin_panel/eleve_form.html"

    def get(self, request, pk):
        eleve = get_object_or_404(Eleve, pk=pk)
        form = EleveForm(instance=eleve)
        return render(request, self.template_name, {"form": form, "eleve": eleve, "action": "Modifier"})

    def post(self, request, pk):
        eleve = get_object_or_404(Eleve, pk=pk)
        form = EleveForm(request.POST, instance=eleve)
        if form.is_valid():
            try:
                form.save_with_user(existing_eleve=eleve)
                messages.success(request, f"Élève « {eleve.nom_complet} » modifié avec succès.")
                return redirect("admin_panel:eleves")
            except Exception as e:
                form.add_error(None, str(e))
        return render(request, self.template_name, {"form": form, "eleve": eleve, "action": "Modifier"})


@directeur_required_dispatch
class EleveDeleteView(View):
    def post(self, request, pk):
        eleve = get_object_or_404(Eleve, pk=pk)
        nom = eleve.nom_complet
        user = eleve.user
        eleve.delete()
        user.delete()
        messages.success(request, f"Élève « {nom} » supprimé avec succès.")
        return redirect("admin_panel:eleves")


# ─── PROFESSEURS ───────────────────────────────────────────────────────────────

@directeur_required_dispatch
class ProfesseursAdminView(View):
    template_name = "admin_panel/professeurs.html"

    def get(self, request):
        professeurs = Professeur.objects.select_related("user").prefetch_related("cours")
        prof_data = []
        for prof in professeurs:
            nb_cours = prof.cours.count()
            prof_data.append({"prof": prof, "nb_cours": nb_cours})
        context = {"prof_data": prof_data}
        return render(request, self.template_name, context)


@directeur_required_dispatch
class ProfesseurCreateView(View):
    template_name = "admin_panel/professeur_form.html"

    def get(self, request):
        form = ProfesseurCreateForm()
        return render(request, self.template_name, {"form": form, "action": "Ajouter"})

    def post(self, request):
        form = ProfesseurCreateForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    prof = form.save()
                messages.success(
                    request,
                    f"Professeur « {prof.nom_complet} » créé avec succès. "
                    f"Identifiant : {prof.user.identifiant}",
                )
                return redirect("admin_panel:professeurs")
            except Exception as e:
                form.add_error(None, str(e))
        return render(request, self.template_name, {"form": form, "action": "Ajouter"})


@directeur_required_dispatch
class ProfesseurEditView(View):
    template_name = "admin_panel/professeur_form.html"

    def get(self, request, pk):
        prof = get_object_or_404(Professeur, pk=pk)
        form = ProfesseurEditForm(instance=prof)
        return render(request, self.template_name, {"form": form, "prof": prof, "action": "Modifier"})

    def post(self, request, pk):
        prof = get_object_or_404(Professeur, pk=pk)
        form = ProfesseurEditForm(request.POST, instance=prof)
        if form.is_valid():
            form.save()
            messages.success(request, f"Professeur « {prof.nom_complet} » modifié avec succès.")
            return redirect("admin_panel:professeurs")
        return render(request, self.template_name, {"form": form, "prof": prof, "action": "Modifier"})


@directeur_required_dispatch
class ProfesseurDeleteView(View):
    def post(self, request, pk):
        prof = get_object_or_404(Professeur, pk=pk)
        nom = prof.nom_complet
        user = prof.user
        prof.delete()
        user.delete()
        messages.success(request, f"Professeur « {nom} » supprimé avec succès.")
        return redirect("admin_panel:professeurs")


# ─── COURS ─────────────────────────────────────────────────────────────────────

@directeur_required_dispatch
class CoursAdminView(View):
    template_name = "admin_panel/cours.html"

    def get(self, request):
        cours = Cours.objects.select_related("professeur", "classe").order_by("classe__niveau", "nom")
        context = {"cours": cours}
        return render(request, self.template_name, context)


@directeur_required_dispatch
class CoursCreateView(View):
    template_name = "admin_panel/cours_form.html"

    def get(self, request):
        form = CoursForm()
        return render(request, self.template_name, {"form": form, "action": "Ajouter"})

    def post(self, request):
        form = CoursForm(request.POST)
        if form.is_valid():
            cours = form.save()
            messages.success(request, f"Cours « {cours.nom} » ajouté avec succès.")
            return redirect("admin_panel:cours")
        return render(request, self.template_name, {"form": form, "action": "Ajouter"})


@directeur_required_dispatch
class CoursEditView(View):
    template_name = "admin_panel/cours_form.html"

    def get(self, request, pk):
        cours = get_object_or_404(Cours, pk=pk)
        form = CoursForm(instance=cours)
        return render(request, self.template_name, {"form": form, "cours": cours, "action": "Modifier"})

    def post(self, request, pk):
        cours = get_object_or_404(Cours, pk=pk)
        form = CoursForm(request.POST, instance=cours)
        if form.is_valid():
            form.save()
            messages.success(request, f"Cours « {cours.nom} » modifié avec succès.")
            return redirect("admin_panel:cours")
        return render(request, self.template_name, {"form": form, "cours": cours, "action": "Modifier"})


@directeur_required_dispatch
class CoursDeleteView(View):
    def post(self, request, pk):
        cours = get_object_or_404(Cours, pk=pk)
        nom = cours.nom
        cours.delete()
        messages.success(request, f"Cours « {nom} » supprimé avec succès.")
        return redirect("admin_panel:cours")


# ─── PAIEMENTS ─────────────────────────────────────────────────────────────────

@directeur_required_dispatch
class PaiementsAdminView(View):
    template_name = "admin_panel/paiements.html"

    def get(self, request):
        statut = request.GET.get("statut")
        mois = request.GET.get("mois")
        moyen = request.GET.get("moyen")

        qs = Paiement.objects.select_related("eleve", "frais", "eleve__classe").order_by("-date_paiement")

        if statut:
            qs = qs.filter(statut=statut)
        if mois:
            qs = qs.filter(frais__mois=mois)
        if moyen:
            qs = qs.filter(moyen_paiement=moyen)

        total_filtre = qs.filter(statut="paye").aggregate(total=Sum("montant"))["total"] or 0

        context = {
            "paiements": qs[:200],
            "total_filtre": total_filtre,
            "statut_choices": Paiement.STATUT_CHOICES,
            "mode_choices": Paiement.MODE_CHOICES,
            "mois_choices": FraisScolaire.MOIS_CHOICES,
            "statut_actif": statut,
            "mois_actif": mois,
            "moyen_actif": moyen,
        }
        return render(request, self.template_name, context)


# ─── NOTES (consultation directeur) ───────────────────────────────────────────

@directeur_required_dispatch
class NotesAdminView(View):
    template_name = "admin_panel/notes.html"

    def get(self, request):
        classe_id = request.GET.get("classe")
        cours_id = request.GET.get("cours")

        cours_qs = Cours.objects.select_related("professeur", "classe").order_by("classe__niveau", "nom")
        classes = Classe.objects.all()

        notes = Note.objects.select_related(
            "eleve", "eleve__classe",
            "evaluation_cours__cours",
            "evaluation_cours__evaluation",
        ).order_by(
            "evaluation_cours__cours__classe__niveau",
            "evaluation_cours__cours__nom",
            "eleve__nom",
        )

        if classe_id:
            notes = notes.filter(eleve__classe_id=classe_id)
        if cours_id:
            notes = notes.filter(evaluation_cours__cours_id=cours_id)

        if classe_id:
            cours_qs = cours_qs.filter(classe_id=classe_id)

        context = {
            "notes": notes[:500],
            "classes": classes,
            "cours_list": cours_qs,
            "classe_actif": classe_id,
            "cours_actif": cours_id,
            "total_notes": notes.count(),
        }
        return render(request, self.template_name, context)
