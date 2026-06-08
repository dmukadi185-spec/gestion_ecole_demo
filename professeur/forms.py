from django import forms

from dashboard.models import Note


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
        if note_max is not None:
            self.fields["valeur"].widget.attrs["max"] = str(note_max)
            self.fields["valeur"].help_text = f"Note max : {note_max}"
