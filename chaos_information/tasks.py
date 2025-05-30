import logging
import openai
from celery import shared_task
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from .models import TextInput, Information
from .services.information_service import create_information_for_text_input, create_information
from chaos_embeddings.services.clustering_service import trigger_clustering
from chaos_embeddings.services.embedding_service import save_embedding_for_object

logger = logging.getLogger(__name__)
openai.api_key = settings.OPENAI_API_KEY

@shared_task
def handle_information_creation_task(model_label: str, obj_pk: str):
    """
    Wird gerufen, wenn ein neues Kind-Objekt angelegt wurde.
    Ruft create_information(obj) auf.
    """
    app_label, model_name = model_label.split('.')
    ct = ContentType.objects.get(app_label=app_label, model=model_name.lower())
    Model = ct.model_class()
    obj = Model.objects.get(pk=obj_pk)
    # Erzeuge oder aktualisiere Information:
    create_information(obj, meta_text="")

@shared_task
def update_information_embedding_task(info_pk: str, update_fields: list[str]):
    """
    Wird gerufen, wenn Felder einer Information aktualisiert wurden.
    Generiert ein neues Embedding und speichert es, dann clustert neu.
    """
    info = Information.objects.get(pk=info_pk)
    # Nur danken, wenn relevante Felder geändert wurden
    texts = [
        info.title or "",
        info.context or "",
        info.information_short or "",
        info.information_long or "",
    ]
    text = "\n".join(filter(None, texts))
    # Speichere Embedding im eigenen Modell
    save_embedding_for_object(info, text)
    # Re-Clustering
    trigger_clustering()


@shared_task(bind=True, default_retry_delay=10, max_retries=5)
def task_create_information_for_text_input(self, text_input_pk: str):
    """
    Holt das TextInput-Objekt per PK und übergibt es samt Text
    an create_information_for_text_input.
    """
    logger.info(f"[task] Starte TextInput-Task für {text_input_pk}")
    try:
        text_obj = TextInput.objects.get(pk=text_input_pk)
    except TextInput.DoesNotExist:
        logger.error(f"[task] TextInput {text_input_pk} nicht gefunden")
        return None

    try:
        return create_information_for_text_input(text_obj)
    except Exception as e:
        logger.exception(f"[task] Fehler bei TextInput {text_input_pk}: {e}")
        raise self.retry(exc=e)