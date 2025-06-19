from django import forms
from .models import DailyJournal


class DailyJournalForm(forms.ModelForm):
    class Meta:
        model = DailyJournal
        fields = [
            'date',
            'meta_description',
            'daily_summary',
            'positive_things',
            'negative_things',
            'daily_thoughts',
        ]
        widgets = {
            'date': forms.DateTimeInput(attrs={
                'type': 'datetime-local',
                'class': 'form-control'
            }),
            'meta_description': forms.Textarea(attrs={
                'rows': 2,
                'class': 'form-control'
            }),
            'daily_summary': forms.Textarea(attrs={
                'rows': 3,
                'class': 'form-control'
            }),
            'positive_things': forms.Textarea(attrs={
                'rows': 3,
                'class': 'form-control'
            }),
            'negative_things': forms.Textarea(attrs={
                'rows': 3,
                'class': 'form-control'
            }),
            'daily_thoughts': forms.Textarea(attrs={
                'rows': 4,
                'class': 'form-control'
            }),
        }
