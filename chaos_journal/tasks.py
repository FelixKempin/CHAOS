from celery import shared_task
from .services.information_service import logger, create_information_for_journal



@shared_task(bind=True, default_retry_delay=10, max_retries=5)
def task_create_info_for_journal(self, journal_pk):
    logger.info(f"[task_create_info_for_journal] Task gestartet für Journal{journal_pk}")
    try:
        from .models import DailyJournal
        journal = DailyJournal.objects.get(pk=journal_pk)
        return create_information_for_journal(journal)

    except self.MaxRetriesExceededError:
        logger.error(f"[task_create_info_for_goal] Max. Retry-Anzahl erreicht für {journal_pk} – Aufgabe abgebrochen")
    except Exception as e:
        logger.exception(f"[task_create_info_for_goal] Fehler für Ziel {journal_pk}: {e}")
        raise
