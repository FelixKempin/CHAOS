import logging
from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import (
    IMG_Document, PDF_Document, TEXT_Document,
)
from .tasks import (
    task_create_info_for_img,
    task_create_info_for_pdf,
    task_create_info_for_text,
)

logger = logging.getLogger(__name__)

# --- IMG_Document → Information Creation ---
@receiver(post_save, sender=IMG_Document)
def handle_img_doc_save(sender, instance: IMG_Document, created, **kwargs):
    """
    Bei neuem Image-Dokument: enqueuet Task zur Anlage einer Information.
    """
    if created and instance.file:
        transaction.on_commit(
            lambda: task_create_info_for_img.delay(str(instance.pk))
        )
        logger.debug(f"[signals] scheduled task_create_info_for_img for IMG_Document {instance.pk}")

# --- PDF_Document → Information Creation ---
@receiver(post_save, sender=PDF_Document)
def handle_pdf_doc_save(sender, instance: PDF_Document, created, **kwargs):
    """
    Bei neuem PDF-Dokument: enqueuet Task zur Anlage einer Information.
    """
    if created and instance.file:
        transaction.on_commit(
            lambda: task_create_info_for_pdf.delay(str(instance.pk))
        )
        logger.debug(f"[signals] scheduled task_create_info_for_pdf for PDF_Document {instance.pk}")

# --- TEXT_Document → Information Creation ---
@receiver(post_save, sender=TEXT_Document)
def handle_text_doc_save(sender, instance: TEXT_Document, created, **kwargs):
    """
    Bei neuem Text-Dokument: enqueuet Task zur Anlage einer Information.
    """
    if created and instance.file:
        transaction.on_commit(
            lambda: task_create_info_for_text.delay(str(instance.pk))
        )
        logger.debug(f"[signals] scheduled task_create_info_for_text for TEXT_Document {instance.pk}")
