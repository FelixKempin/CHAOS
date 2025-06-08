# chaos_documents/forms.py
from django import forms
from .models import MARKDOWN_Document

class MarkdownDocumentForm(forms.ModelForm):
    class Meta:
        model = MARKDOWN_Document
        fields = ['name', 'meta_description']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Titel'
            }),
            'meta_description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Kurze Beschreibung'
            }),
        }
