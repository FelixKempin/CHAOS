# main_app/models.py
import uuid
from django.db import models
from chaos_embeddings.models import Embedding  # Dein bereits vorhandenes Embedding‐Model


class Thread(models.Model):
    """
    Ein Chat-Thread / Verlauf.
    """
    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title       = models.CharField("Titel", max_length=150)
    created_at  = models.DateTimeField("Erstellt am", auto_now_add=True, db_index=True)
    updated_at  = models.DateTimeField("Zuletzt aktualisiert", auto_now=True, db_index=True)

    def __str__(self):
        return self.title

class ChatMessage(models.Model):
    """
    Einzelne Nachricht innerhalb eines Threads.
    """
    SENDER_CHOICES = [
        ('user',      'User'),
        ('assistant','Assistant'),
    ]

    thread     = models.ForeignKey(Thread, related_name='messages', on_delete=models.CASCADE)
    sender     = models.CharField("Wer", max_length=20, choices=SENDER_CHOICES, db_index=True)
    content    = models.TextField("Inhalt")
    created_at = models.DateTimeField("Gesendet am", auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"[{self.get_sender_display()}] {self.content[:50]}"
