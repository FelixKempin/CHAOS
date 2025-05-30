import logging
import os
import openai
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from openai import OpenAI

from ..models import Embedding
from chaos_information.models import Information

logger = logging.getLogger(__name__)
openai.api_key = os.environ.get("OPENAI_API_KEY", settings.OPENAI_API_KEY)

client = OpenAI(api_key=settings.OPENAI_API_KEY)
def generate_embedding(text: str):
    resp = client.embeddings.create(
        model=settings.OPEN_AI_MODEL_EMBEDDING,
        input=text
    )
    # resp.data ist eine Liste; wir nehmen das erste Ergebnis
    return resp.data[0].embedding


def save_embedding_for_object(obj, text: str, model: str = None) -> Embedding:
    """
    Erzeugt via OpenAI ein Embedding für `text` und speichert es
    in chaos_embeddings.models.Embedding unter GenericForeignKey auf `obj`.
    """
    # Modell wählen
    if model is None:
        model = settings.OPEN_AI_MODEL_EMBEDDING
    # Embedding generieren
    vector = generate_embedding(text)
    # ContentType des Objekts
    ct = ContentType.objects.get_for_model(obj)
    # Eintrag anlegen oder updaten
    emb, created = Embedding.objects.update_or_create(
        content_type=ct,
        object_id=str(obj.pk),
        defaults={'vector': vector}
    )
    logger.debug(
        f"{'Created' if created else 'Updated'} Embedding for "
        f"{ct.app_label}.{ct.model} pk={obj.pk}"
    )
    return emb