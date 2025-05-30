# my_ai_app/forms.py

from django import forms
from django.urls import reverse_lazy
from dal import autocomplete

from .models import Information, Tag, Vault

class InformationForm(forms.ModelForm):
    class Meta:
        model = Information
        fields = [
            'title',
            'status',
            'vault',
            'draft',
            'folder',
            'tags',
            'information_short',
            'information_long',
            'information_original',
        ]
        widgets = {
            'vault': forms.Select(attrs={'class': 'form-select'}),
            'folder': forms.Select(attrs={'class': 'form-select'}),
            'tags': autocomplete.ModelSelect2Multiple(
                url=reverse_lazy('tag-autocomplete'),
                attrs={
                    'data-placeholder': 'Tags auswählen…',
                    'data-minimum-input-length': 1,
                }
            ),
        }


# erlaubte Quell-Modelle für object_type_string
DOC_MODELS = [
    'img_document',
    'pdf_document',
    'csv_document',
    'text_document',
    'markdown_document',
    'audio_document',
    'textinput',
]

class InformationFilterForm(forms.Form):
    q = forms.CharField(
        required=False, label='Titel',
        widget=forms.TextInput(attrs={
            'placeholder': 'Titel…',
            'class': 'form-control form-control-sm'
        })
    )
    text = forms.CharField(
        required=False, label='Text',
        widget=forms.TextInput(attrs={
            'placeholder': 'Text…',
            'class': 'form-control form-control-sm'
        })
    )
    tags = forms.ModelMultipleChoiceField(
        required=False,
        queryset=Tag.objects.none(),  # wird in __init__ gesetzt
        widget=forms.MultipleHiddenInput()
    )
    vault = forms.ModelChoiceField(
        required=False, label='Vault',
        queryset=Vault.objects.filter(active=True).order_by('name'),
        widget=forms.Select(attrs={'class': 'form-select form-select-sm'})
    )
    date_from = forms.DateField(
        required=False, label='Von Datum',
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control form-control-sm'
        })
    )
    date_to = forms.DateField(
        required=False, label='Bis Datum',
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control form-control-sm'
        })
    )
    status = forms.ChoiceField(
        required=False, label='Status',
        choices=[('', '— alle —')] + Information.STATUS_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select form-select-sm'})
    )


    object_type = forms.ChoiceField(
        required=False,
        label='Objekttyp',
        choices=[],  # wird in __init__ gesetzt
        widget=forms.Select(attrs={'class': 'form-select form-select-sm'})
    )
    min_relevance = forms.IntegerField(
        required=False, label='Min. Relevanz',
        min_value=0, max_value=100,
        widget=forms.NumberInput(attrs={
            'placeholder': '0–100',
            'class': 'form-control form-control-sm'
        })
    )
    order = forms.ChoiceField(
        required=False, label='Sortierung',
        choices=[
            ('-datetime', 'Datum absteigend'),
            ('datetime', 'Datum aufsteigend'),
            ('relevance', 'Relevanz'),
        ],
        widget=forms.Select(attrs={'class': 'form-select form-select-sm'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Tags laden
        self.fields['tags'].queryset = Tag.objects.all().order_by('name')

        # Single-Select-Choices für object_type
        LABELS = {
            'img_document': 'Image-Dokument',
            'pdf_document': 'PDF-Dokument',
            'csv_document': 'CSV-Dokument',
            'text_document': 'Text-Dokument',
            'markdown_document': 'Markdown-Dokument',
            'audio_document': 'Audio-Dokument',
            'textinput': 'Text-Input',
        }
        choices = [('', '— alle —')]
        for key in DOC_MODELS:
            label = LABELS.get(key, key.replace('_', ' ').title())
            choices.append((key, label))
        self.fields['object_type'].choices = choices

    def clean_order(self):
        order = self.cleaned_data.get('order')
        return 'relevance' if order == 'relevance' else order

