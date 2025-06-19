# main_app/models.py
import uuid
from django.db import models
from chaos_embeddings.models import Embedding  # Dein bereits vorhandenes Embedding‐Model

from chaos_information.models import Information


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


# models.py
class ThreadContextEntry(models.Model):
    """
    Feste Kontext-Zuordnung für einen Thread zu einer Information.
    Speichert auch, welches Attribut (short/long/original) verwendet wird.
    """
    ATTRIBUTE_CHOICES = [
        ('information_short',    'Kurz'),
        ('information_long',     'Lang'),
        ('information_original', 'Original'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    thread = models.ForeignKey(Thread, on_delete=models.CASCADE, related_name='context_entries')
    information = models.ForeignKey(Information, on_delete=models.CASCADE)
    selected_attribute = models.CharField(max_length=30, choices=ATTRIBUTE_CHOICES)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('thread', 'information')  # keine doppelten Infos pro Thread

    def get_content(self):
        """
        Gibt den gewählten Attributinhalt zurück – oder fällt dynamisch zurück.
        """
        # Versuche, das gewählte Attribut zu laden
        content = getattr(self.information, self.selected_attribute, '').strip()

        # Fallback: falls leer, dynamisch tiefer gehen
        if not content:
            fallback_order = {
                'information_short':    ['information_long', 'information_original'],
                'information_long':     ['information_original'],
                'information_original': [],
            }
            for fallback in fallback_order[self.selected_attribute]:
                content = getattr(self.information, fallback, '').strip()
                if content:
                    self.selected_attribute = fallback
                    self.save(update_fields=['selected_attribute'])
                    break
        return content
