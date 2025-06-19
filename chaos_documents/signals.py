import logging

from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from django.db.models.signals import post_save, pre_save, pre_delete, post_delete
from .models import IMG_Document, PDF_Document, TEXT_Document, EmbeddedAsset
from .tasks import (
    task_create_info_for_img,
    task_create_info_for_pdf,
    task_create_info_for_text,
    task_create_info_for_markdown,
)
import re
from django.db.models.signals import pre_delete
from django.dispatch import receiver
from .models import MARKDOWN_Document
from chaos_embeddings.services.embedding_service import update_embedding_for_information
from chaos_information.models import Information

logger = logging.getLogger(__name__)

DOCUMENT_MODELS = [
    IMG_Document,
    PDF_Document,
    TEXT_Document,
    MARKDOWN_Document,
    EmbeddedAsset,
]

def register_file_signals(model):
    model_name = model.__name__

    @receiver(pre_save, sender=model)
    def delete_old_file_on_change(sender, instance, **kwargs):
        """Löscht alte Datei beim Update, wenn der Name sich geändert hat."""
        if not instance.pk:
            return  # Neue Instanz, nichts zu löschen
        try:
            old_instance = sender.objects.get(pk=instance.pk)
        except sender.DoesNotExist:
            return
        old_file = getattr(old_instance, 'file', None)
        new_file = getattr(instance, 'file', None)

        if (
            old_file and old_file.name
            and new_file and old_file.name != new_file.name
        ):
            try:
                logger.debug(f"[{model_name}] Alte Datei wird ersetzt: {old_file.name}")
                old_file.delete(save=False)
            except Exception as e:
                logger.error(f"[{model_name}] Fehler beim Löschen alter Datei: {e}", exc_info=True)

    @receiver(pre_delete, sender=model)
    def delete_file_on_delete(sender, instance, **kwargs):
        file_field = getattr(instance, 'file', None)
        if file_field:
            logger.warning(f"🧪 Lösche Datei (raw): {file_field.name}")
            try:
                # GCS direkt ansprechen
                file_field.storage.delete(file_field.name)
                logger.warning(f"✅ Datei gelöscht: {file_field.name}")
            except Exception as e:
                logger.error(f"❌ Fehler beim direkten Löschen: {e}", exc_info=True)
        else:
            logger.warning("⚠️ Kein file_field gefunden oder leer")


for model in DOCUMENT_MODELS:
    register_file_signals(model)

# --- Informationen erzeugen ---

@receiver(post_save, sender=IMG_Document)
def handle_img_doc_save(sender, instance: IMG_Document, created, **kwargs):
    if created and instance.file:
        transaction.on_commit(
            lambda: task_create_info_for_img.delay(str(instance.pk))
        )
        logger.debug(f"[signals] task_create_info_for_img scheduled für IMG_Document {instance.pk}")

@receiver(post_save, sender=PDF_Document)
def handle_pdf_doc_save(sender, instance: PDF_Document, created, **kwargs):
    if created and instance.file:
        transaction.on_commit(
            lambda: task_create_info_for_pdf.delay(str(instance.pk))
        )
        logger.debug(f"[signals] task_create_info_for_pdf scheduled für PDF_Document {instance.pk}")

@receiver(post_save, sender=TEXT_Document)
def handle_text_doc_save(sender, instance: TEXT_Document, created, **kwargs):
    if created and instance.file:
        transaction.on_commit(
            lambda: task_create_info_for_text.delay(str(instance.pk))
        )
        logger.debug(f"[signals] task_create_info_for_text scheduled für TEXT_Document {instance.pk}")


@receiver(post_save, sender=MARKDOWN_Document)
def handle_markdown_doc_save(sender, instance, created, **kwargs):
    ## DIE Originalinformation muss bei dieser gelegenheit noch jedes mal aus dem md gezogen werden -> keine AI nötig

    if not instance.file:
        return

    ct = ContentType.objects.get_for_model(instance)

    try:
        info = Information.objects.get(content_type=ct, object_id=str(instance.pk))
    except Information.DoesNotExist:
        info = None

    if created or info is None:
        # Erstelle komplett via Task
        transaction.on_commit(
            lambda: task_create_info_for_markdown.delay(str(instance.pk))
        )
        logger.debug(f"[signals] task_create_info_for_markdown scheduled (create) für {instance.pk}")
    else:
        # Update: nur Embedding updaten
        def update_embeddings():
            # Nutze die Logik für Embedding-Update mit dem vorhandenen Information-Objekt
            update_embedding_for_information(info)

        transaction.on_commit(update_embeddings)
        logger.debug(f"[signals] Embedding-Update für MARKDOWN_Document {instance.pk} durchgeführt")

@receiver(post_delete, sender=MARKDOWN_Document)
def cleanup_on_delete(sender, instance, **kwargs):
    # Alle EmbeddedAssets löschen (diese kümmern sich selbst um ihre Datei!)
    instance.embedded_assets.all().delete()

    # Markdown-Datei selbst löschen
    if instance.file and instance.file.name:
        try:
            instance.file.delete(save=False)
        except Exception:
            pass