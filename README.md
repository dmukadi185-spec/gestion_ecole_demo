# Lycée Étoile Brillante — Plateforme Scolaire

Application web Django de gestion scolaire avec quatre portails distincts : élèves, espace directeur, espace professeur et admin Django.

---

## Arborescence du projet

```
plateforme_ecole/          ← Configuration centrale Django
├── settings.py            ← Paramètres (BDD, apps, Jazzmin, sessions…)
├── urls.py                ← Routage racine + patch admin superuser
├── wsgi.py / asgi.py      ← Points d'entrée serveur

accounts/                  ← Modèles utilisateurs, auth, formulaires
├── models.py              ← User, Eleve, Classe, Directeur
├── views.py               ← home, SignInView, activate_account, SignOutView
├── forms.py               ← SignInForm, StaffSignInForm, DirecteurSignInForm, ActivateAccountForm
├── urls.py                ← /comptes/connexion/, /activation/, /deconnexion/
├── utils.py               ← normalize_identifiant, get_eleve_for_user
└── admin.py               ← Enregistrement des modèles dans Django admin

dashboard/                 ← Portail élève (notes, résultats)
├── models.py              ← Cours, Evaluation, EvaluationCours, Note
├── views.py               ← index (accueil élève), resultats
├── urls.py                ← /dashboard/, /dashboard/resultats/
└── admin.py               ← Enregistrement notes, cours, évaluations

payments/                  ← Module paiements élève
├── models.py              ← FraisScolaire, Paiement
├── views.py               ← liste_paiements, effectuer_paiement, recu
├── forms.py               ← PaiementForm (contrôle paiement mensuel séquentiel)
├── urls.py                ← /paiements/, /paiements/nouveau/, /paiements/<pk>/recu/
└── admin.py               ← Enregistrement paiements, frais scolaires

admin_panel/               ← Tableau de bord directeur (lecture + filtres)
├── views.py               ← AdminLoginView, DashboardAdminView, ElevesAdminView, PaiementsAdminView
└── urls.py                ← /administration/, /administration/connexion/, /eleves/, /paiements/

professeur/                ← Tableau de bord professeur
├── views.py               ← ProfesseurLoginView, DashboardProfesseurView, CoursProfesseurView, ClassesProfesseurView, ElevesProfesseurView, CoursNotesView, NoteEditView
├── forms.py               ← NoteForm
└── urls.py                ← /professeur/, /professeur/connexion/, /professeur/cours/, /professeur/classes/, /professeur/eleves/

templates/                 ← Tous les templates HTML
├── base.html              ← Template de base élèves (Bootstrap 5.3.3)
├── home.html              ← Page d'accueil publique avec formulaire login
├── admin/index.html       ← Dashboard Django admin personnalisé (cartes modèles)
├── accounts/              ← signin.html, activate_account.html, no_eleve_profile.html
├── dashboard/             ← dashboard.html, resultats.html
├── payments/              ← paiements.html, effectuer_paiement.html, recu.html
├── admin_panel/           ← base_admin.html, login.html, dashboard.html, eleves.html, paiements.html
└── professeur/            ← login.html, dashboard.html, cours.html, classes.html, eleves.html, notes.html, note_form.html

static/
├── css/style.css          ← Styles portail élève
├── css/admin.css          ← Styles dashboards directeur/professeur (gradient cards, Inter font)
└── img/logo-ecole.svg     ← Logo SVG de l'école
```

---

## Liens d'accès aux pages

| Page | URL | Accès requis |
|------|-----|--------------|
| Accueil / Login élève | `/` | Public |
| Connexion élève | `/comptes/connexion/` | Public |
| Activation compte élève | `/comptes/activation/` | Public (élèves sans mot de passe) |
| Déconnexion | `/comptes/deconnexion/` | Authentifié |
| **Dashboard élève** | `/dashboard/` | Élève connecté |
| Résultats / Notes | `/dashboard/resultats/` | Élève connecté |
| Historique paiements | `/paiements/` | Élève connecté |
| Effectuer un paiement | `/paiements/nouveau/` | Élève connecté |
| Reçu de paiement | `/paiements/<id>/recu/` | Élève connecté |
| **Connexion Directeur** | `/administration/connexion/` | Public → Directeur |
| Dashboard Directeur | `/administration/` | Profil `Directeur` |
| Liste élèves Directeur | `/administration/eleves/` | Profil `Directeur` |
| Paiements Directeur | `/administration/paiements/` | Profil `Directeur` |
| **Connexion Professeur** | `/professeur/connexion/` | Public → Professeur |
| Dashboard Professeur | `/professeur/` | Profil `Professeur` |
| Cours Professeur | `/professeur/cours/` | Profil `Professeur` |
| Classes Professeur | `/professeur/classes/` | Profil `Professeur` |
| Élèves Professeur | `/professeur/eleves/` | Profil `Professeur` |
| **Admin Django** | `/admin/` | `is_superuser=True` uniquement |

---

## Stack technique

| Outil | Version | Rôle | Pourquoi ce choix |
|-------|---------|------|-------------------|
| **Django** | 6.0.6 | Framework web | ORM puissant, admin intégré, système d'auth extensible |
| **SQLite** | — | Base de données | Fichier unique, zéro config, suffisant pour usage scolaire |
| **django-jazzmin** | 3.0.4 | Redesign Django admin | Interface AdminLTE moderne sans réécrire l'admin |
| **WhiteNoise** | 6.12.0 | Fichiers statiques | Sert CSS/JS sans Nginx en dev et en production |
| **Gunicorn** | 26.0.0 | Serveur WSGI production | Standard Python WSGI, compatible Replit/Render |
| **Bootstrap** | 5.3.3 | UI CSS | CDN, responsive, compatible mobile |
| **Chart.js** | 4.4.4 | Graphiques | Graphiques interactifs paiements/stats côté navigateur |

---

## Modèles de données

### `accounts` — Identité et rôles

```
User (AbstractBaseUser + PermissionsMixin)
├── identifiant      : CharField unique  ← "NOM POSTNOM PRENOM" normalisé majuscules
├── is_active        : BooleanField
├── is_staff         : BooleanField       ← accès /administration/
├── is_superuser     : BooleanField       ← accès /admin/ Django uniquement
└── password_created : BooleanField       ← False = compte pas encore activé par l'élève

Classe
├── niveau      : CharField  ← ex: "6ème"
└── departement : CharField  ← ex: "Math-Physique"

Eleve  (OneToOne → User)
├── nom / postnom / prenom : CharField
└── classe : ForeignKey → Classe (nullable)

Directeur  (OneToOne → User)
├── nom / postnom / prenom : CharField (optionnels)
└── titre : choices → directeur_general | directeur_adjoint | censeur | prefet | autre
```

**Règle clé :** L'identifiant d'un élève est généré automatiquement : `NOM POSTNOM PRENOM` en majuscules. Exemple : `MUKENDI KABONGO JEAN`. Si le nom change, l'identifiant est resynchronisé (`sync_user_identifiant`).

### `dashboard` — Académique

```
Cours
└── nom : CharField  ← "Mathématiques", "Français"…

Evaluation
├── type    : interrogation | examen
├── periode : 1p | 2p | 3p | 4p | exam1 | exam2
└── semestre: calculé automatiquement à la sauvegarde
              (1p/2p/exam1 → "1", reste → "2")

EvaluationCours  (liaison Cours × Evaluation)
├── note_max    : DecimalField  ← barème (ex: 20)
└── ponderation : DecimalField  ← poids en % (ex: 30.00)
Contrainte : unique_together (cours, evaluation)

Note
├── eleve           : ForeignKey → Eleve
├── evaluation_cours: ForeignKey → EvaluationCours
└── valeur          : DecimalField
Contrainte : unique_together (eleve, evaluation_cours)
```

### `payments` — Paiements scolaires

```
FraisScolaire
├── type_frais : minerval | autre
├── mois       : septembre | octobre | … | juin
└── montant    : DecimalField
Contrainte : unique_together (type_frais, mois)

Paiement
├── eleve             : ForeignKey → Eleve
├── frais             : ForeignKey → FraisScolaire
├── moyen_paiement    : orange | airtel | mpesa
├── montant           : copié automatiquement depuis frais.montant à la sauvegarde
├── statut            : en_attente | paye | echec
├── date_paiement     : auto_now_add
└── numero_transaction: généré auto → "PMT20260608091523123456"
Contrainte : unique_together (eleve, frais) → un élève ne paie qu'une fois par mois
```

---

## Flux d'authentification complet

### 1 — Création du compte élève (par le superadmin)
Le superadmin va sur `/admin/accounts/eleve/add/`. Django crée automatiquement un `User` avec `password_created=False` via `save_model` dans `EleveAdmin`.

### 2 — Activation du compte par l'élève
L'élève va sur `/comptes/activation/` et remplit `ActivateAccountForm` :

```python
# ActivateAccountForm.clean_identifiant()
user = User.objects.get(identifiant=identifiant)      # identifiant existe ?
Eleve.objects.filter(user=user).exists()              # profil élève associé ?
if user.password_created: raise ValidationError(...)  # déjà activé ?

# .save() → set_password + password_created=True + login automatique
```

### 3 — Connexions suivantes (login élève)

```
POST / ou POST /comptes/connexion/
    └── SignInForm.clean()
            ├── authenticate(identifiant, password)  → User ou None
            ├── Vérifie user.is_active
            ├── Vérifie user.password_created
            └── Si ni staff ni directeur → vérifie Eleve.objects.filter(user=user)

    _get_redirect_for_user(user) :
        user.is_staff=True         →  /administration/
        user.directeur existe      →  /administration/
        sinon (élève)              →  /dashboard/
```

### 4 — Formulaires séparés par rôle

| Formulaire | Utilisé sur | Vérification spéciale |
|------------|-------------|----------------------|
| `SignInForm` | `/` et `/comptes/connexion/` | Bloque si pas `Eleve` (sauf staff/directeur) |
| `DirecteurSignInForm` | `/administration/connexion/` | Authentification pure — rôle vérifié dans la vue |
| `ProfesseurSignInForm` | `/professeur/connexion/` | Authentification pure — rôle vérifié dans la vue |

---

## Protection des vues (contrôle d'accès)

### Portail élève — décorateur Django standard
```python
@login_required(login_url="accounts:signin")
def index(request):
    eleve = get_eleve_for_user(request.user)  # None si pas de profil Eleve
    if eleve is None:
        return render_no_eleve_profile(request)  # → 403 avec template dédié
```

### Portail directeur — décorateur maison sur CBV
```python
@directeur_required_dispatch  # vérifie request.user.directeur (OneToOne)
class DashboardAdminView(View):
    # Si pas de profil Directeur → redirect /administration/connexion/?next=<url>
```

### Portail professeur — décorateur maison sur CBV
```python
@professeur_required_dispatch  # vérifie request.user.professeur (OneToOne)
class DashboardProfesseurView(View):
    # Si pas de profil Professeur → redirect /professeur/connexion/?next=<url>
```

### Django admin `/admin/` — patch de classe
```python
# plateforme_ecole/urls.py — appliqué au démarrage
def _superuser_only(self, request):
    return request.user.is_active and request.user.is_superuser

admin.site.__class__.has_permission = _superuser_only
# Un staff non-superuser est redirigé vers /admin/login/ avec son propre écran
```

---

## Logique métier importante

### Paiements séquentiels (pas de saut de mois)
```python
MONTH_ORDER = ["septembre", "octobre", "novembre", "decembre",
               "janvier", "fevrier", "mars", "avril", "mai", "juin"]

# Dans effectuer_paiement() :
prochain_frais = next(
    (f for f in frais_list if f.id not in paiements_deja_payes),
    None
)
# Le formulaire ne propose QUE ce mois — impossible de sauter octobre pour payer novembre
```

### Génération automatique de l'identifiant élève
```python
@staticmethod
def generate_identifiant(nom, postnom, prenom):
    parts = [nom.strip(), postnom.strip(), prenom.strip()]
    return " ".join(" ".join(parts).split()).upper()
# "mukendi  kabongo jean" → "MUKENDI KABONGO JEAN"
```

### Calcul du semestre (auto à la sauvegarde)
```python
def save(self, *args, **kwargs):
    self.semestre = "1" if self.periode in {"1p", "2p", "exam1"} else "2"
    if not self.nom:
        self.nom = f"{self.get_type_display()} - {self.get_periode_display()}"
    super().save(*args, **kwargs)
```

### Numéro de transaction automatique
```python
self.numero_transaction = timezone.now().strftime("PMT%Y%m%d%H%M%S%f")
# Exemple → PMT20260608091523123456
```

### Montant copié automatiquement depuis le barème
```python
def save(self, *args, **kwargs):
    if self.frais_id and not self.montant:
        self.montant = self.frais.montant  # copié une seule fois à la création
    if self.frais_id and not self.description:
        self.description = f"{self.frais.get_type_frais_display()} mois de {self.frais.get_mois_display()}"
    super().save(*args, **kwargs)
```

---

## Requêtes ORM clés (dashboards)

Les vues admin/directeur et professeur font des agrégations Django ORM sérialisées en JSON pour Chart.js :

```python
# Total encaissé
total = Paiement.objects.filter(statut="paye").aggregate(total=Sum("montant"))["total"]

# Encaissements par mois (graphique barres)
Paiement.objects.filter(statut="paye")
    .values("frais__mois")
    .annotate(total=Sum("montant"), nombre=Count("id"))

# Taux de paiement par classe
payes = Paiement.objects.filter(eleve__classe=cls, statut="paye")
    .values("eleve").distinct().count()
taux = round((payes / nb_eleves) * 100)

# Élèves sans aucun paiement
Eleve.objects.filter(paiements__isnull=True).count()

# Répartition par moyen de paiement
Paiement.objects.filter(statut="paye")
    .values("moyen_paiement")
    .annotate(total=Sum("montant"), nombre=Count("id"))
```

---

## Comptes disponibles

| Identifiant | Rôle | Connexion via |
|-------------|------|---------------|
| `ADMIN` | Superuser | `/admin/` |
| `DIRECTEUR-GEN` | Directeur | `/administration/` |
| `DIRECTEUR1` | Directeur | `/administration/` |
| `PROF-DOE` | Professeur | `/professeur/` |
| `MUKENDI KABONGO JEAN` | Élève | `/dashboard/` |

---

## Installation en local

```bash
# 1. Installer les dépendances
pip install -r requirements.txt

# 2. Appliquer les migrations
python manage.py migrate

# 3. Créer le superadmin
python manage.py createsuperuser
# Identifiant : ADMIN (majuscules)

# 4. Lancer le serveur
python manage.py runserver 0.0.0.0:5000
```

### Dépendances (`requirements.txt`)
```
asgiref==3.11.1
Django==6.0.6
django-jazzmin==3.0.4
gunicorn==26.0.0
packaging==26.2
sqlparse==0.5.5
whitenoise==6.12.0
```

---

## Variables d'environnement

| Variable | Défaut | Rôle |
|----------|--------|------|
| `DJANGO_DEBUG` | `True` | Mode debug Django |
| `REPLIT_DEV_DOMAIN` | auto (Replit) | Ajouté à `CSRF_TRUSTED_ORIGINS` |
| `RENDER_EXTERNAL_HOSTNAME` | — | Pour déploiement Render |

---

*Lycée Étoile Brillante — Plateforme scolaire Django*
