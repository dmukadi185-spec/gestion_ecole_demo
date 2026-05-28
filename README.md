# Plateforme numérique scolaire

Plateforme Django minimaliste pour la consultation des notes et des paiements par les élèves.

## Installation

```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
```

## Lancement

```bash
python manage.py runserver
```

Accès : http://127.0.0.1:8000/

## Administration

1. Créer une **classe** si nécessaire (`/admin/`).
2. Créer un **élève** (`Eleve`) en renseignant nom, postnom et prénom : un compte `User` est créé automatiquement avec l'identifiant `NOM POSTNOM PRENOM` en majuscules (ex. Dupont / Mbuya / Kabongo → `DUPONT MBUYA KABONGO`), sans mot de passe (`password_created` = False).
3. Ajouter cours, évaluations, notes et paiements via `/admin/`.

L'élève active son compte via **Créer mon mot de passe** sur la page d'accueil (identifiant en majuscules, parties séparées par des espaces).

## URLs principales

| URL | Description |
|-----|-------------|
| `/` | Landing page publique |
| `/comptes/connexion/` | Connexion |
| `/comptes/activation/` | Création du mot de passe |
| `/dashboard/` | Tableau de bord élève |
| `/dashboard/resultats/` | Consultation des notes |
| `/paiements/` | Historique des paiements |
| `/admin/` | Administration Django |
