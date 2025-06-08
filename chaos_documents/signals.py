import logging
from django.db import transaction
from django.db.models.signals import post_save, pre_save, pre_delete
from django.dispatch import receiver

from .models import IMG_Document, PDF_Document, TEXT_Document
from .tasks import (
    task_create_info_for_img,
    task_create_info_for_pdf,
    task_create_info_for_text,
)

logger = logging.getLogger(__name__)

DOCUMENT_MODELS = [
    IMG_Document,
    PDF_Document,
    TEXT_Document,
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
