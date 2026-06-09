from django.urls import path

from . import views

app_name = "professeur"

urlpatterns = [
    path("connexion/", views.ProfesseurLoginView.as_view(), name="login"),
    path("", views.DashboardProfesseurView.as_view(), name="index"),
    path("cours/", views.CoursProfesseurView.as_view(), name="cours"),
    path("classes/", views.ClassesProfesseurView.as_view(), name="classes"),
    path("eleves/", views.ElevesProfesseurView.as_view(), name="eleves"),
    path("cours/<int:cours_pk>/notes/", views.CoursNotesView.as_view(), name="cours_notes"),
    path(
        "evaluation/<int:eval_cours_pk>/eleve/<int:eleve_pk>/note/ajouter/",
        views.NoteAddView.as_view(),
        name="note_add",
    ),
    path("notes/<int:pk>/modifier/", views.NoteEditView.as_view(), name="note_edit"),
    path("notes/<int:pk>/supprimer/", views.NoteDeleteView.as_view(), name="note_delete"),
]
