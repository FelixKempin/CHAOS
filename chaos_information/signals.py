import logging

from django.conf import settings
from django.db import transaction
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from django.contrib.contenttypes.models import ContentType

from .models import Information, Tag, TextInput, RelevanceEvent
from .tasks import (
    update_information_embedding_task,
    handle_information_creation_task,
    task_create_information_for_text_input
)
from chaos_embeddings.models import Embedding
from chaos_embeddings.services.embedding_service import generate_embedding
from openai import OpenAI

logger = logging.getLogger(__name__)

client = OpenAI(api_key=settings.OPENAI_API_KEY)


@receiver(post_delete, sender=Information)
def delete_embedding_and_source(sender, instance, **kwargs):
    """
    Wenn eine Information gelöscht wird:
    1) lösche das zugehörige Embedding
    2) lösche das Quell-Objekt (Dokument, TextInput, etc.)
    3) lösche alle RelevanceEvents zu dieser Information
    """
    # 1) Embedding entfernen
    ct_info = ContentType.objects.get_for_model(Information)
    deleted, _ = Embedding.objects.filter(
        content_type=ct_info,
        object_id=str(instance.pk)
    ).delete()
    logger.debug(f"Deleted {deleted} Embedding(s) for Information {instance.pk}")

    # 2) Quell-Objekt löschen
    try:
        src = instance.content_object
        if src:
            # Wenn Dokument: Datei vor dem Löschen entfernen!
            if hasattr(src, 'file') and src.file:
                logger.warning(f"Lösche Datei aus Storage direkt: {src.file.name}")
                try:
                    src.file.delete(save=False)
                except Exception as e:
                    logger.error(f"Fehler beim Löschen der Datei: {e}", exc_info=True)
            src.delete()
            logger.debug(
                f"Deleted source object "
                f"{instance.content_type.model} (pk={instance.object_id})"
            )
    except Exception:
        logger.exception(
            f"Fehler beim Löschen des Quell-Objekts "
            f"{instance.content_type.model} (pk={instance.object_id})"
        )

    # 3) RelevanceEvents löschen
    relevance_events_deleted, _ = RelevanceEvent.objects.filter(
        information=instance
    ).delete()
    logger.debug(f"Deleted {relevance_events_deleted} RelevanceEvent(s) for Information {instance.pk}")
@receiver(post_save, sender=Information)
def on_information_saved(sender, instance, created, update_fields, **kwargs):
    # 3) Beim Update relevanter Felder: nur das Embedding neu berechnen
    relevant = {'title', 'context', 'information_short', 'information_long'}
    if update_fields and relevant.intersection(update_fields):
        transaction.on_commit(
            lambda: update_information_embedding_task.delay(
                info_pk=str(instance.pk),
                update_fields=list(update_fields)
            )
        )

@receiver(post_save, sender=Tag)
def ensure_description_and_embedding(sender, instance: Tag, created, **kwargs):
    """
    Erzeuge per OpenAI kurze Beschreibung und speichere Tag-Embedding.
    """
    updated = {}
    if created or not instance.description:
        try:
            prompt = f"Bitte kurze Beschreibung für Tag '{instance.name}'."
            resp = client.chat.completions.create(
                model=settings.OPEN_AI_MODEL_CLASSIFY,
                messages=[
                    {"role": "system", "content": "Nur Text ohne JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.0, max_tokens=60
            )
            updated['description'] = resp.choices[0].message.content.strip()
        except Exception:
            logger.exception("Tag-Description fehlgeschlagen")

    try:
        emb_input = f"{instance.name} {updated.get('description', instance.description or '')}".strip()
        vector = generate_embedding(emb_input)
        ct_tag = ContentType.objects.get_for_model(Tag)
        Embedding.objects.update_or_create(
            content_type=ct_tag,
            object_id=str(instance.pk),
            defaults={'vector': vector}
        )
    except Exception:
        logger.exception("Tag-Embedding fehlgeschlagen")

    if updated:
        Tag.objects.filter(pk=instance.pk).update(**updated)

@receiver(post_save, sender=TextInput)
def handle_text_input_save(sender, instance: TextInput, created, **kwargs):
    """
    Bei neuem TextInput: enqueuet Task zur Anlage einer Information.
    """
    if created and instance.text:
        transaction.on_commit(
            lambda: task_create_information_for_text_input.delay(str(instance.pk))
        )
        logger.debug(f"[signals] scheduled task_create_info_for_text_input for TextInput {instance.pk}")

