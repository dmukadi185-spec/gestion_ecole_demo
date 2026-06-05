from django.contrib.auth import login
from django.db.models import Count, Sum, Q
from django.db.models.functions import TruncMonth
from django.shortcuts import redirect, render
from django.views import View

from accounts.forms import SignInForm
from accounts.models import Classe, Eleve, User
from dashboard.models import Cours, Note
from payments.models import FraisScolaire, Paiement


def staff_required(view_func=None):
    """Decorator: redirects to admin login page if user is not authenticated staff."""
    def decorator(func):
        from functools import wraps
        @wraps(func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated or not request.user.is_staff:
                return redirect(f"/administration/connexion/?next={request.path}")
            return func(request, *args, **kwargs)
        return wrapper
    return decorator if view_func is None else decorator(view_func)


def staff_required_dispatch(cls):
    """Class-based view decorator for staff-only access."""
    original_dispatch = cls.dispatch

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_staff:
            return redirect(f"/administration/connexion/?next={request.path}")
        return original_dispatch(self, request, *args, **kwargs)

    cls.dispatch = dispatch
    return cls


class AdminLoginView(View):
    template_name = "admin_panel/login.html"

    def get(self, request):
        if request.user.is_authenticated and request.user.is_staff:
            return redirect("/administration/")
        form = SignInForm(request)
        return render(request, self.template_name, {"form": form})

    def post(self, request):
        form = SignInForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            if not user.is_staff:
                return render(request, self.template_name, {
                    "form": form,
                    "error": "Ce compte n'a pas accès au panneau d'administration.",
                })
            login(request, user)
            next_url = request.GET.get("next", "/administration/")
            return redirect(next_url)
        return render(request, self.template_name, {"form": form})


MOIS_ORDER = [
    "septembre", "octobre", "novembre", "decembre",
    "janvier", "fevrier", "mars", "avril", "mai", "juin",
]


@staff_required_dispatch
class DashboardAdminView(View):
    template_name = "admin_panel/dashboard.html"

    def get(self, request):
        # --- Statistiques générales ---
        total_eleves = Eleve.objects.count()
        total_classes = Classe.objects.count()
        total_cours = Cours.objects.count()
        eleves_actifs = User.objects.filter(is_active=True, is_staff=False).count()

        # --- Finances globales ---
        paiements_qs = Paiement.objects.filter(statut="paye")
        total_encaisse = paiements_qs.aggregate(total=Sum("montant"))["total"] or 0

        # Total attendu (frais × élèves par frais défini)
        total_frais_definis = FraisScolaire.objects.aggregate(total=Sum("montant"))["total"] or 0
        total_attendu = total_frais_definis * total_eleves if total_eleves else 0

        total_en_attente_montant = Paiement.objects.filter(statut="en_attente").aggregate(
            total=Sum("montant")
        )["total"] or 0

        total_echec = Paiement.objects.filter(statut="echec").count()

        # --- Paiements par statut ---
        paiements_par_statut = (
            Paiement.objects.values("statut")
            .annotate(nombre=Count("id"), montant_total=Sum("montant"))
            .order_by("statut")
        )
        statut_labels = []
        statut_data = []
        statut_colors = {"paye": "#1a4d8c", "en_attente": "#f0ad4e", "echec": "#dc3545"}
        for s in paiements_par_statut:
            statut_labels.append(dict(Paiement.STATUT_CHOICES).get(s["statut"], s["statut"]))
            statut_data.append(float(s["montant_total"] or 0))

        # --- Paiements par mois (selon MOIS_ORDER) ---
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

        # --- Paiements par moyen ---
        par_moyen = (
            Paiement.objects.filter(statut="paye")
            .values("moyen_paiement")
            .annotate(total=Sum("montant"), nombre=Count("id"))
        )
        moyen_labels = []
        moyen_data = []
        moyen_colors = ["#1a4d8c", "#28a745", "#fd7e14"]
        for p in par_moyen:
            label = dict(Paiement.MODE_CHOICES).get(p["moyen_paiement"], p["moyen_paiement"] or "N/A")
            moyen_labels.append(label)
            moyen_data.append(float(p["total"] or 0))

        # --- Taux de paiement par classe ---
        classes = Classe.objects.prefetch_related("eleve_set").all()
        taux_par_classe = []
        for cls in classes:
            eleves_cls = cls.eleve_set.count()
            if eleves_cls == 0:
                continue
            payes = Paiement.objects.filter(
                eleve__classe=cls, statut="paye"
            ).values("eleve").distinct().count()
            taux = round((payes / eleves_cls) * 100) if eleves_cls > 0 else 0
            taux_par_classe.append({
                "classe": str(cls),
                "eleves": eleves_cls,
                "payes": payes,
                "taux": taux,
            })

        # --- Élèves sans aucun paiement ---
        eleves_sans_paiement = Eleve.objects.filter(
            paiements__isnull=True
        ).select_related("classe").count()

        # --- Derniers paiements ---
        derniers_paiements = (
            Paiement.objects.select_related("eleve", "frais", "eleve__classe")
            .order_by("-date_paiement")[:15]
        )

        # --- Récapitulatif par type de frais ---
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
            type_frais_data.append({
                "label": label,
                "total": float(t["total"] or 0),
                "nombre": t["nombre"],
            })

        context = {
            # Stats générales
            "total_eleves": total_eleves,
            "total_classes": total_classes,
            "total_cours": total_cours,
            "eleves_actifs": eleves_actifs,
            # Finances
            "total_encaisse": total_encaisse,
            "total_en_attente_montant": total_en_attente_montant,
            "total_echec": total_echec,
            # Charts
            "statut_labels": statut_labels,
            "statut_data": statut_data,
            "mois_labels": mois_labels,
            "mois_data": mois_data,
            "mois_nombres": mois_nombres,
            "moyen_labels": moyen_labels,
            "moyen_data": moyen_data,
            "moyen_colors": moyen_colors,
            # Tableaux
            "taux_par_classe": taux_par_classe,
            "eleves_sans_paiement": eleves_sans_paiement,
            "derniers_paiements": derniers_paiements,
            "type_frais_data": type_frais_data,
        }
        return render(request, self.template_name, context)


@staff_required_dispatch
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
            montant_paye = eleve.paiements.filter(statut="paye").aggregate(
                total=Sum("montant")
            )["total"] or 0
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


@staff_required_dispatch
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
