# organizer_agent_app/forms.py
from django import forms
from .models import Appointment, ToDo

class AppointmentForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = [
            'title', 'description',
            'begin', 'end',
            'priority',
            'frequency', 'interval', 'by_weekday', 'end_date',
        ]
        widgets = {
            'begin': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class':'form-control'}),
            'end':   forms.DateTimeInput(attrs={'type': 'datetime-local', 'class':'form-control'}),
            'description': forms.Textarea(attrs={'class':'form-control', 'rows':3}),
        }

class ToDoForm(forms.ModelForm):
    class Meta:
        model = ToDo
        fields = [
            'title', 'description', 'deadline',
            'priority', 'dependencies',
            'frequency', 'interval', 'by_weekday', 'end_date',
        ]
        widgets = {
            'deadline': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class':'form-control'}),
            'description': forms.Textarea(attrs={'class':'form-control', 'rows':3}),
            'dependencies': forms.SelectMultiple(attrs={'class':'form-select'}),
        }
