from django import forms


class ChatForm(forms.Form):
    text = forms.CharField(
        label="Nachricht",
        widget=forms.Textarea(attrs={
            "rows": 2,
            "placeholder": "Text hier eingeben…",
            "class": "form-control"
        }),
        required=False
    )
    file = forms.FileField(label="Datei", required=False)
    image = forms.ImageField(
        label="Bild",
        required=False,
        widget=forms.ClearableFileInput(attrs={
            "accept": "image/*",
            "capture": "environment",
            "class": "form-control"
        })
    )

    def clean(self):
        cleaned = super().clean()
        text = cleaned.get('text')
        file = cleaned.get('file')
        image = cleaned.get('image')

        if not any([text, file, image]):
            raise forms.ValidationError("Bitte Text, Datei oder Bild eingeben.")
        if file and image:
            raise forms.ValidationError("Entweder Datei oder Bild, nicht beides.")
        return cleaned
