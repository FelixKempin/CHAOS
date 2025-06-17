from django import forms
from .models import Goal, GoalStatusUpdate

class GoalForm(forms.ModelForm):
    class Meta:
        model = Goal
        fields = ['type', 'name', 'meta_description', 'definition_description', 'definition_conditions']

class GoalStatusUpdateForm(forms.ModelForm):
    class Meta:
        model = GoalStatusUpdate
        fields = ['goal', 'content']
        widgets = {
            'goal': forms.HiddenInput(),
            'content': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }
