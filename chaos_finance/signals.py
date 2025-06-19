import logging


from django.db import transaction
from django.db.models.signals import post_save



from .models import Goal, GoalStatusUpdate, Advice
from .tasks import task_create_info_for_goal, task_create_info_for_advice, \
    task_create_info_for_goal_status_update

from django.dispatch import receiver

logger = logging.getLogger(__name__)


# --- Informationen erzeugen ---

@receiver(post_save, sender=Goal)
def handle_goal_save(sender, instance: Goal, created, **kwargs):
    if created:
        transaction.on_commit(
            lambda: task_create_info_for_goal.delay(str(instance.pk))
        )
        logger.debug(f"[signals] task_create_info_for_img scheduled für IMG_Document {instance.pk}")


"""
@receiver(post_save, sender=Advice)
def handle_goal_status_update_save(sender, instance: Advice, created, **kwargs):
    if created and instance.content:
        transaction.on_commit(
            lambda: task_create_info_for_goal_status_update.delay(str(instance.pk))
        )
        logger.debug(f"[signals] task_create_info_for_pdf scheduled für PDF_Document {instance.pk}")

@receiver(post_save, sender=GoalStatusUpdate)
def handle_advice_save(sender, instance: GoalStatusUpdate, created, **kwargs):
    if created and instance.content:
        transaction.on_commit(
            lambda: task_create_info_for_advice.delay(str(instance.pk))
        )
        logger.debug(f"[signals] task_create_info_for_text scheduled für TEXT_Document {instance.pk}")
"""