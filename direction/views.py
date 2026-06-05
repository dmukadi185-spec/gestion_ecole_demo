from functools import wraps

from django.contrib.auth import login
from django.db.models import Avg, Count, Sum
from django.shortcuts import redirect, render
from django.views import View

from accounts.forms import SignInForm
from accounts.models import Classe, Eleve
from dashboard.models import Cours, Note
from payments.models import FraisScolaire, Paiement


MOIS_ORDER = [
    "septembre", "octobre", "novembre", "decembre",
    "janvier", "fevrier", "mars", "avril", "mai", "juin",
]


def directeur_required(view_func=None):
    """Decorator: only users with a Directeur profile can access."""
    def decorator(func):
        @wraps(func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect(f"/comptes/connexion/?next={request.path}")
            try:
                _ = request.user.directeur
            except Exception:
                return redirect("home")
            return func(request, *args, **kwargs)
        return wrapper
    return decorator if view_func is None else decorator(view_func)


def directeur_required_dispatch(cls):
    """Class-based view decorator — redirects to direction login."""
    original_dispatch = cls.dispatch

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(f"/direction/connexion/?next={request.path}")
        try:
            _ = request.user.directeur
        except Exception:
            return redirect(f"/direction/connexion/")
        return original_dispatch(self, request, *args, **kwargs)

    cls.dispatch = dispatch
    return cls


class DirecteurLoginView(View):
    template_name = "direction/login.html"

    def get(self, request):
        try:
            if request.user.is_authenticated and request.user.directeur:
                return redirect("/direction/")
        except Exception:
            pass
        form = SignInForm(request)
        return render(request, self.template_name, {"form": form})

    def post(self, request):
        form = SignInForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            try:
                _ = user.directeur
            except Exception:
                return render(request, self.template_name, {
                    "form": form,
                    "error": "Ce compte n'a pas accès à l'espace direction.",
                })
            login(request, user)
            next_url = request.GET.get("next", "/direction/")
            return redirect(next_url)
        return render(request, self.template_name, {"form": form})


def _build_finance_context():
    """Shared financial data for all director views."""
    paiements_qs = Paiement.objects.filter(statut="paye")

    total_encaisse = paiements_qs.aggregate(total=Sum("montant"))["total"] or 0
    total_en_attente = Paiement.objects.filter(statut="en_attente").aggregate(total=Sum("montant"))["total"] or 0
    total_echec_nb = Paiement.objects.filter(statut="echec").count()

    # Par mois
    par_mois_qs = (
        paiements_qs.values("frais__mois")
        .annotate(total=Sum("montant"), nombre=Count("id"))
    )
    mois_dict = {p["frais__mois"]: p for p in par_mois_qs}
    mois_labels, mois_data, mois_nombres = [], [], []
    for m in MOIS_ORDER:
        label = dict(FraisScolaire.MOIS_CHOICES).get(m, m.capitalize())
        mois_labels.append(label)
        mois_data.append(float(mois_dict.get(m, {}).get("total", 0)))
        mois_nombres.append(mois_dict.get(m, {}).get("nombre", 0))

    # Par moyen
    par_moyen = (
        paiements_qs.values("moyen_paiement")
        .annotate(total=Sum("montant"), nombre=Count("id"))
    )
    moyen_labels, moyen_data = [], []
    for p in par_moyen:
        label = dict(Paiement.MODE_CHOICES).get(p["moyen_paiement"], p["moyen_paiement"] or "N/A")
        moyen_labels.append(label)
        moyen_data.append(float(p["total"] or 0))

    # Par statut
    par_statut = (
        Paiement.objects.values("statut")
        .annotate(nombre=Count("id"), montant_total=Sum("montant"))
    )
    statut_labels, statut_data = [], []
    for s in par_statut:
        statut_labels.append(dict(Paiement.STATUT_CHOICES).get(s["statut"], s["statut"]))
        statut_data.append(float(s["montant_total"] or 0))

    return dict(
        total_encaisse=total_encaisse,
        total_en_attente=total_en_attente,
        total_echec_nb=total_echec_nb,
        mois_labels=mois_labels,
        mois_data=mois_data,
        mois_nombres=mois_nombres,
        moyen_labels=moyen_labels,
        moyen_data=moyen_data,
        statut_labels=statut_labels,
        statut_data=statut_data,
    )


@directeur_required_dispatch
class DashboardDirecteurView(View):
    template_name = "direction/dashboard.html"

    def get(self, request):
        directeur = request.user.directeur

        # --- General stats ---
        total_eleves = Eleve.objects.count()
        total_classes = Classe.objects.count()
        total_cours = Cours.objects.count()
        eleves_sans_paiement = Eleve.objects.filter(paiements__isnull=True).count()

        # --- Per-class breakdown ---
        classes = Classe.objects.prefetch_related("eleve_set").all()
        par_classe = []
        for cls in classes:
            nb = cls.eleve_set.count()
            payes = Paiement.objects.filter(eleve__classe=cls, statut="paye").values("eleve").distinct().count()
            montant_cls = Paiement.objects.filter(eleve__classe=cls, statut="paye").aggregate(t=Sum("montant"))["t"] or 0
            taux = round((payes / nb) * 100) if nb > 0 else 0
            par_classe.append({"classe": str(cls), "nb_eleves": nb, "payes": payes, "taux": taux, "montant": montant_cls})

        # Finance
        fin = _build_finance_context()

        # Recent payments
        derniers = (
            Paiement.objects.select_related("eleve", "frais", "eleve__classe")
            .order_by("-date_paiement")[:12]
        )

        context = {
            "directeur": directeur,
            "total_eleves": total_eleves,
            "total_classes": total_classes,
            "total_cours": total_cours,
            "eleves_sans_paiement": eleves_sans_paiement,
            "par_classe": par_classe,
            "derniers_paiements": derniers,
            **fin,
        }
        return render(request, self.template_name, context)


@directeur_required_dispatch
class FinancesDirecteurView(View):
    template_name = "direction/finances.html"

    def get(self, request):
        directeur = request.user.directeur

        # Type frais recap
        par_type = (
            Paiement.objects.filter(statut="paye")
            .values("frais__type_frais")
            .annotate(total=Sum("montant"), nombre=Count("id"))
        )
        type_frais = []
        for t in par_type:
            label = dict(FraisScolaire.TYPE_CHOICES).get(t["frais__type_frais"], t["frais__type_frais"] or "Autre")
            type_frais.append({"label": label, "total": float(t["total"] or 0), "nombre": t["nombre"]})

        # Per-class finance
        classes = Classe.objects.all()
        finance_par_classe = []
        for cls in classes:
            encaisse = Paiement.objects.filter(eleve__classe=cls, statut="paye").aggregate(t=Sum("montant"))["t"] or 0
            en_attente = Paiement.objects.filter(eleve__classe=cls, statut="en_attente").aggregate(t=Sum("montant"))["t"] or 0
            nb_eleves = cls.eleve_set.count()
            finance_par_classe.append({
                "classe": str(cls),
                "nb_eleves": nb_eleves,
                "encaisse": float(encaisse),
                "en_attente": float(en_attente),
            })

        # All payments list
        paiements = Paiement.objects.select_related("eleve", "frais", "eleve__classe").order_by("-date_paiement")[:100]

        fin = _build_finance_context()

        context = {
            "directeur": directeur,
            "type_frais": type_frais,
            "finance_par_classe": finance_par_classe,
            "paiements": paiements,
            **fin,
        }
        return render(request, self.template_name, context)


@directeur_required_dispatch
class ElevesDirecteurView(View):
    template_name = "direction/eleves.html"

    def get(self, request):
        directeur = request.user.directeur
        classe_id = request.GET.get("classe")

        classes = Classe.objects.all()
        eleves_qs = Eleve.objects.select_related("user", "classe").prefetch_related("paiements")
        if classe_id:
            eleves_qs = eleves_qs.filter(classe_id=classe_id)

        eleves_data = []
        for eleve in eleves_qs:
            nb_payes = eleve.paiements.filter(statut="paye").count()
            montant = eleve.paiements.filter(statut="paye").aggregate(t=Sum("montant"))["t"] or 0
            eleves_data.append({"eleve": eleve, "nb_payes": nb_payes, "montant": float(montant)})

        context = {
            "directeur": directeur,
            "eleves_data": eleves_data,
            "classes": classes,
            "classe_selectionnee": classe_id,
        }
        return render(request, self.template_name, context)
