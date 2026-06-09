from django.urls import path

from . import views

app_name = "admin_panel"

urlpatterns = [
    path("connexion/", views.AdminLoginView.as_view(), name="login"),
    path("", views.DashboardAdminView.as_view(), name="index"),

    # Élèves
    path("eleves/", views.ElevesAdminView.as_view(), name="eleves"),
    path("eleves/ajouter/", views.EleveCreateView.as_view(), name="eleve_create"),
    path("eleves/<int:pk>/modifier/", views.EleveEditView.as_view(), name="eleve_edit"),
    path("eleves/<int:pk>/supprimer/", views.EleveDeleteView.as_view(), name="eleve_delete"),

    # Professeurs
    path("professeurs/", views.ProfesseursAdminView.as_view(), name="professeurs"),
    path("professeurs/ajouter/", views.ProfesseurCreateView.as_view(), name="professeur_create"),
    path("professeurs/<int:pk>/modifier/", views.ProfesseurEditView.as_view(), name="professeur_edit"),
    path("professeurs/<int:pk>/supprimer/", views.ProfesseurDeleteView.as_view(), name="professeur_delete"),

    # Cours
    path("cours/", views.CoursAdminView.as_view(), name="cours"),
    path("cours/ajouter/", views.CoursCreateView.as_view(), name="cours_create"),
    path("cours/<int:pk>/modifier/", views.CoursEditView.as_view(), name="cours_edit"),
    path("cours/<int:pk>/supprimer/", views.CoursDeleteView.as_view(), name="cours_delete"),

    # Paiements
    path("paiements/", views.PaiementsAdminView.as_view(), name="paiements"),

    # Notes (consultation)
    path("notes/", views.NotesAdminView.as_view(), name="notes"),
]
