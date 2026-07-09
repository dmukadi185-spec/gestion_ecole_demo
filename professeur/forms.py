from django import forms

from dashboard.models import Note
from django.core.exceptions import ValidationError
from decimal import Decimal


class NoteForm(forms.ModelForm):
    class Meta:
        model = Note
        fields = ["valeur"]
        widgets = {
            "valeur": forms.NumberInput(
                attrs={"class": "form-control", "step": "0.5", "min": "0", "style": "max-width:120px;"}
            )
        }

    def __init__(self, *args, note_max=None, **kwargs):
        super().__init__(*args, **kwargs)
        # keep note_max for server-side validation
        self.note_max = note_max
        if note_max is not None:
            self.fields["valeur"].widget.attrs["max"] = str(note_max)
            self.fields["valeur"].help_text = f"Note max : {note_max}"

    def clean_valeur(self):
        val = self.cleaned_data.get("valeur")
        if val is None:
            return val
        if self.note_max is not None:
            try:
                if Decimal(str(val)) > Decimal(str(self.note_max)):
                    raise ValidationError(f"La valeur ne peut pas dépasser la note maximale ({self.note_max}).")
            except ValidationError:
                raise
            except Exception:
                # fallback: if conversion fails, let model validation handle it
                pass
        return val
