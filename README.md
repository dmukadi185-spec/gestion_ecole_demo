# Lycée Étoile Brillante — Plateforme numérique scolaire

Plateforme Django complète pour la gestion scolaire : portail élève, panneau d'administration staff, et espace direction.

---

## Stack technique

- **Backend** : Django 6.0.6 (Python)
- **Base de données** : SQLite (fichier local `db.sqlite3`)
- **Frontend** : Bootstrap 5.3.3, Bootstrap Icons 1.11.3, Chart.js 4.4.4
- **Fichiers statiques** : WhiteNoise
- **Serveur** : `manage.py runserver 0.0.0.0:5000`

---

## Installation

```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver 0.0.0.0:5000
```

---

## Architecture des apps Django

| App | Description |
|-----|-------------|
| `accounts` | Modèles User, Eleve, Classe, Directeur + auth |
| `dashboard` | Notes, cours, évaluations (portail élève) |
| `payments` | Paiements, frais scolaires, reçus |
| `admin_panel` | Panneau d'administration staff |
| `direction` | Tableau de bord directeurs |

---

## URLs et chemins d'accès

### Pages publiques

| URL | Description |
|-----|-------------|
| `/` | Landing page publique (formulaire de connexion) |
| `/comptes/connexion/` | Connexion générale |
| `/comptes/activation/` | Activation du compte élève (création du mot de passe) |
| `/comptes/deconnexion/` | Déconnexion |

### Portail élève (authentification requise)

| URL | Description |
|-----|-------------|
| `/dashboard/` | Tableau de bord élève (notes récentes, paiements récents) |
| `/dashboard/resultats/` | Consultation des notes et évaluations |
| `/paiements/` | Historique des paiements |
| `/paiements/<pk>/recu/` | Reçu de paiement (impression / PDF) |

### Panneau d'administration (compte staff requis)

| URL | Description |
|-----|-------------|
| `/administration/connexion/` | **Page de connexion dédiée** au panel admin |
| `/administration/` | Vue d'ensemble : stats, finances, graphiques |
| `/administration/eleves/` | Liste des élèves avec filtres et état des paiements |
| `/administration/paiements/` | Historique complet des paiements avec filtres |

### Espace Direction (compte directeur requis)

| URL | Description |
|-----|-------------|
| `/direction/connexion/` | **Page de connexion dédiée** à l'espace direction |
| `/direction/` | Dashboard : stats globales, effectifs par classe, graphiques |
| `/direction/finances/` | Finances détaillées : par mois, type, classe, historique |
| `/direction/eleves/` | Liste des élèves filtrée par classe |

### Administration Django (superutilisateur requis)

| URL | Description |
|-----|-------------|
| `/admin/` | Interface d'administration Django (gestion des modèles) |

---

## Gestion des comptes

### Compte élève
- Créé automatiquement depuis `/admin/` → **Élèves**
- Identifiant = `NOM POSTNOM PRENOM` en majuscules (ex : `DUPONT MBUYA KABONGO`)
- L'élève active son compte via `/comptes/activation/` (crée son mot de passe)
- Après connexion → redirigé vers `/dashboard/`

### Compte staff (administration)
- Créé depuis `/admin/` → **Utilisateurs**, cocher `is_staff = True`
- Connexion via `/administration/connexion/` (page dédiée avec thème navy)
- Accès bloqué si `is_staff = False`
- Après connexion → redirigé vers `/administration/`

### Compte directeur
- Créé depuis `/admin/` → **Directeurs**
- Renseigner : identifiant libre (ex : `DIR-KABONGO`), mot de passe, titre (Directeur Général, Adjoint, Censeur, Préfet des études)
- Nom / postnom / prénom **optionnels** (utilisés pour l'affichage)
- Connexion via `/direction/connexion/` (page dédiée avec thème doré)
- Accès bloqué si le compte n'a pas de profil `Directeur`
- Après connexion → redirigé vers `/direction/`

---

## Redirection intelligente après connexion

Après chaque connexion depuis la page d'accueil (`/`), le système redirige automatiquement selon le profil :

| Profil | Redirection |
|--------|-------------|
| `is_staff = True` | `/administration/` |
| Profil `Directeur` | `/direction/` |
| Élève (défaut) | `/dashboard/` |

---

## Modèles de données

### `accounts.User`
- `identifiant` (CharField, unique, mis en majuscules automatiquement)
- `is_active`, `is_staff`, `is_superuser`, `password_created`

### `accounts.Eleve`
- `user` (OneToOne → User)
- `nom`, `postnom`, `prenom` (CharField)
- `classe` (ForeignKey → Classe, nullable)

### `accounts.Directeur`
- `user` (OneToOne → User)
- `nom`, `postnom`, `prenom` (CharField, **optionnels**)
- `titre` (choices : directeur_general, directeur_adjoint, censeur, prefet, autre)

### `accounts.Classe`
- `niveau`, `departement` (CharField)

### `payments.FraisScolaire`
- `type_frais` (minerval / autre)
- `mois` (septembre → juin)
- `montant` (DecimalField)

### `payments.Paiement`
- `eleve` (ForeignKey → Eleve)
- `frais` (ForeignKey → FraisScolaire, nullable)
- `moyen_paiement` (orange / airtel / mpesa)
- `montant`, `description`, `statut` (en_attente / paye / echec)
- `date_paiement` (auto), `numero_transaction` (auto PMT…)

### `dashboard.Cours`, `dashboard.Evaluation`, `dashboard.Note`
- Cours → Evaluations → Notes (liées aux élèves)

---

## Fonctionnalités principales

### Portail élève
- Tableau de bord avec notes récentes, derniers paiements, profil
- Page des résultats avec filtres (cours / évaluation)
- Historique des paiements avec statuts colorés
- Reçu de paiement professionnel (impression + téléchargement PDF)
- Breadcrumbs et navigation active sur toutes les pages

### Panneau Administration
- Sidebar sombre (navy) réductible, état mémorisé (localStorage)
- Cartes stat animées avec bande colorée et icône
- Cards financières vertes / oranges / rouges
- Graphiques Chart.js : barres mensuelles, anneau statut, anneau moyen de paiement
- Tableau élèves avec filtres classe/statut
- Tableau paiements avec filtres statut/mois/moyen
- Barre de progression du taux de paiement par classe

### Espace Direction
- Thème doré distinct (sidebar navy foncé, accents dorés)
- Session privée : accessible uniquement aux comptes `Directeur`
- Dashboard : effectif total, classes, encaissements, élèves sans paiement
- Taux de paiement et montant encaissé par classe (tableau + barres de progression)
- Graphiques : encaissements mensuels, répartition par statut, par moyen
- Page Finances : détail par type de frais, par classe, historique 100 derniers paiements
- Page Élèves : liste filtrée par classe, carte récapitulative par classe cliquable

---

## Créer les données de test

```bash
python manage.py shell
```

```python
from accounts.models import User, Classe, Directeur

# Créer une classe
c = Classe.objects.create(niveau="6ème", departement="Général")

# Créer un directeur test
u = User.objects.create_user("DIR-TEST", password="test1234", is_active=True, password_created=True)
Directeur.objects.create(user=u, nom="Kabongo", prenom="Jean", titre="directeur_general")
# Connexion : /direction/connexion/ → DIR-TEST / test1234

# Créer un compte staff
s = User.objects.create_user("ADMIN", password="admin1234", is_active=True, is_staff=True, password_created=True)
# Connexion : /administration/connexion/ → ADMIN / admin1234
```
