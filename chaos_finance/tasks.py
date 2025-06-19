from celery import shared_task
from .services.information_service import logger, create_information_for_goal, \
    create_information_for_goal_status_update, create_information_for_advice
from .services.mentor_service import evaluate_goal


# PDF-Task mit Retry-Logik
@shared_task(bind=True, default_retry_delay=10, max_retries=5)
def task_create_info_for_goal(self, goal_pk):
    logger.info(f"[task_create_info_for_goal] Task gestartet für Ziel {goal_pk}")
    try:
        from .models import Goal
        goal = Goal.objects.get(pk=goal_pk)
        evaluate_goal(goal_pk)
        return create_information_for_goal(goal)

    except self.MaxRetriesExceededError:
        logger.error(f"[task_create_info_for_goal] Max. Retry-Anzahl erreicht für {goal_pk} – Aufgabe abgebrochen")
    except Exception as e:
        logger.exception(f"[task_create_info_for_goal] Fehler für Ziel {goal_pk}: {e}")
        raise
# Text-Task mit Retry
@shared_task(bind=True, default_retry_delay=10, max_retries=5)
def task_create_info_for_goal_status_update(self, goal_status_update_pk):
    try:
        logger.info("CELERY CREATE INFO FOR GoalStatusUpdate TASK...")
        from .models import GoalStatusUpdate
        doc = GoalStatusUpdate.objects.get(pk=goal_status_update_pk)
        logger.info("CELERY CREATE INFO FOR GoalStatusUpdate TASK: Erfolgreich abgeschlossen")
        return create_information_for_goal_status_update(doc)
    except Exception as e:
        logger.exception(f"[task_create_info_for_goal_status_update] Fehler für Text-Dokument {goal_status_update_pk}: {e}")
        raise self.retry(exc=e)
# Image-Task mit Retry
@shared_task(bind=True, default_retry_delay=10, max_retries=5)
def task_create_info_for_advice(self, advice_pk):
    try:
        logger.info("CELERY CREATE INFO FOR Advice TASK...")
        from .models import Advice
        advice = Advice.objects.get(pk=advice_pk)
        logger.info("CELERY CREATE INFO FOR Advice TASK: Erfolgreich abgeschlossen")
        return create_information_for_advice(advice)
    except Exception as e:
        logger.exception(f"[task_create_info_for_advice] Fehler für Bild-Dokument {advice_pk}: {e}")
        raise self.retry(exc=e)


