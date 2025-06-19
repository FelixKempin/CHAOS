import logging
from urllib.parse import unquote

from django.db import transaction
from django.db.models.signals import post_save

from .tasks import task_create_info_for_journal

from .models import DailyJournal

from django.dispatch import receiver

logger = logging.getLogger(__name__)


# --- Informationen erzeugen ---

@receiver(post_save, sender=DailyJournal)
def handle_daily_journal_save(sender, instance: DailyJournal, created, **kwargs):
    if created:
        transaction.on_commit(
            lambda: task_create_info_for_journal.delay(str(instance.pk))
        )
        logger.debug(f"[signals] task_create_info_for_journal scheduled für DailyJournal {instance.pk}")
