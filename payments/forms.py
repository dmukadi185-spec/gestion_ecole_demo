from django import forms

from .models import Paiement, FraisScolaire


class PaiementForm(forms.ModelForm):
    class Meta:
        model = Paiement
        fields = ["moyen_paiement", "frais"]

    def __init__(self, *args, allowed_frais=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.allowed_frais = allowed_frais
        if allowed_frais is not None:
            self.fields["frais"].queryset = allowed_frais
            self.fields["frais"].empty_label = None

    def clean_frais(self):
        frais = self.cleaned_data.get("frais")
        if self.allowed_frais is not None and frais not in self.allowed_frais:
            raise forms.ValidationError("Ce mois n'est pas autorisé pour le paiement.")
        return frais
