# main_app/forms.py
from django import forms
from .models import Thread, ChatMessage

class ThreadForm(forms.ModelForm):
    class Meta:
        model = Thread
        fields = ['title']
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': 'Titel des neuen Threads'}),
        }

class ChatMessageForm(forms.ModelForm):
    class Meta:
        model = ChatMessage
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Schreibe deine Nachricht…'
            }),
        }
        labels = {
            'content': '',
        }
