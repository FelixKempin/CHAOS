from celery import shared_task
from .services.information_service import (
    create_information_for_pdf_doc,
    create_information_for_text_doc,
    create_information_for_img_doc, logger, create_information_for_markdown_doc,
)

# PDF-Task mit Retry-Logik
@shared_task(bind=True, default_retry_delay=10, max_retries=5)
def task_create_info_for_pdf(self, doc_pk):
    logger.info(f"[task_create_info_for_pdf] Task gestartet für PDF {doc_pk}")
    try:
        from .models import PDF_Document
        doc = PDF_Document.objects.get(pk=doc_pk)

        if not doc.file or not doc.file.name:
            raise FileNotFoundError("Dateifeld leer oder nicht vorhanden")

        if not doc.file.storage.exists(doc.file.name):
            logger.warning(f"[task_create_info_for_pdf] Datei {doc.file.name} noch nicht im Storage – retry in 10s")
            raise self.retry(exc=Exception("Datei nicht verfügbar"), countdown=10)

        logger.info(f"[task_create_info_for_pdf] Datei gefunden – starte Verarbeitung für {doc.pk}")
        return create_information_for_pdf_doc(doc)

    except self.MaxRetriesExceededError:
        logger.error(f"[task_create_info_for_pdf] Max. Retry-Anzahl erreicht für {doc_pk} – Aufgabe abgebrochen")
    except Exception as e:
        logger.exception(f"[task_create_info_for_pdf] Fehler für PDF {doc_pk}: {e}")
        raise
# Text-Task mit Retry
@shared_task(bind=True, default_retry_delay=10, max_retries=5)
def task_create_info_for_text(self, doc_pk):
    try:
        logger.info("CELERY CREATE INFO FOR TEXT DOC TASK...")
        from .models import TEXT_Document
        doc = TEXT_Document.objects.get(pk=doc_pk)
        logger.info("CELERY CREATE INFO FOR TEXT DOC TASK: Erfolgreich abgeschlossen")
        return create_information_for_text_doc(doc)
    except Exception as e:
        logger.exception(f"[task_create_info_for_text] Fehler für Text-Dokument {doc_pk}: {e}")
        raise self.retry(exc=e)
# Image-Task mit Retry
@shared_task(bind=True, default_retry_delay=10, max_retries=5)
def task_create_info_for_img(self, doc_pk):
    try:
        logger.info("CELERY CREATE INFO FOR IMG DOC TASK...")
        from .models import IMG_Document
        doc = IMG_Document.objects.get(pk=doc_pk)
        logger.info("CELERY CREATE INFO FOR IMG DOC TASK: Erfolgreich abgeschlossen")
        return create_information_for_img_doc(doc)
    except Exception as e:
        logger.exception(f"[task_create_info_for_img] Fehler für Bild-Dokument {doc_pk}: {e}")
        raise self.retry(exc=e)



# --- Celery-Task mit Retry-Logik für Markdown ---
@shared_task(bind=True, default_retry_delay=10, max_retries=5)
def task_create_info_for_markdown(self, doc_pk):
    logger.info(f"[task_create_info_for_markdown] Task gestartet für MD {doc_pk}")
    try:
        # erst das Model laden
        from .models import MARKDOWN_Document
        doc = MARKDOWN_Document.objects.get(pk=doc_pk)
        logger.info(f"[task_create_info_for_markdown] Datei gefunden – starte Verarbeitung für {doc.pk}")
        return create_information_for_markdown_doc(doc)
    except Exception as e:
        logger.exception(f"[task_create_info_for_markdown] Fehler für MD {doc_pk}: {e}")
        # sofern es kein MaxRetriesExceededError war, retry
        raise
