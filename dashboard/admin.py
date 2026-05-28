from django.contrib import admin

from .models import Cours, Evaluation, EvaluationCours, Note


@admin.register(Cours)
class CoursAdmin(admin.ModelAdmin):
    search_fields = ("nom",)


@admin.register(Evaluation)
class EvaluationAdmin(admin.ModelAdmin):
    list_display = ("nom", "type", "periode", "semestre")
    list_filter = ("type", "periode", "semestre")
    search_fields = ("nom",)


@admin.register(EvaluationCours)
class EvaluationCoursAdmin(admin.ModelAdmin):
    list_display = ("cours", "evaluation", "note_max", "ponderation")
    list_filter = ("cours", "evaluation")
    search_fields = ("cours__nom", "evaluation__nom")
    autocomplete_fields = ("cours", "evaluation")


@admin.register(Note)
class NoteAdmin(admin.ModelAdmin):
    list_display = ("eleve", "evaluation_cours", "valeur")
    list_filter = ("evaluation_cours__cours", "evaluation_cours__evaluation")
    search_fields = ("eleve__nom", "eleve__prenom", "evaluation_cours__cours__nom")
    autocomplete_fields = ("eleve", "evaluation_cours")
