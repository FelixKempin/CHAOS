# my_ai_app/tasks.py

import json
import logging
from celery import shared_task
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from django.conf import settings
import openai

from chaos_embeddings.services.clustering_service import trigger_clustering
from chaos_embeddings.services.embedding_service import generate_embedding
from chaos_information.models import Information
from chaos_information.services.information_service import create_information_for_text_input, \
    create_information_for_required_information

logger = logging.getLogger(__name__)
openai.api_key = settings.OPENAI_API_KEY
"""
def classify_actions(text: str) -> list[str]:
    options = "\n".join(
        f"- {name}: {meta['description']}"
        for name, meta in ACTION_REGISTRY.items()
    )
    prompt = (
        "Aus folgenden Aktionen wähle alle aus, die auf den Text passen (oder []):\n"
        f"{options}\n\n"
        f"TEXT:\n{text}\n\n"
        "Antwort als JSON-Array:"
    )
    resp = openai.ChatCompletion.create(
        model=settings.OPEN_AI_MODEL_CLASSIFY,
        messages=[
            {"role": "system", "content": "Nur ein JSON-Array mit Aktionsnamen."},
            {"role": "user",   "content": prompt},
        ],
        temperature=0.0,
        max_tokens=300,
    )
    raw = resp.choices[0].message.content.strip().lstrip("```").rstrip("```")
    try:
        names = json.loads(raw)
        return [n for n in names if n in ACTION_REGISTRY]
    except Exception as e:
        logger.error(f"classify_actions parse error: {e} / raw={raw}")
        return []

@shared_task
def evaluate_informations():
    logger.info("Starte evaluate_informations-Task")
    now = timezone.now()
    infos = Information.objects.filter(evaluated=False)

    for info in infos:
        try:
            chosen = classify_actions(info.information_long)
            if chosen:
                for name in chosen:
                    aa = AgentAction.objects.create(
                        name=name,
                        function_name=name,
                        information_id=str(info.pk),
                        status='waiting',
                        parameters={},  # keine weiteren Parameter benötigt
                        created_at=now
                    )
                    logger.info(f"AgentAction {aa.pk} für Info {info.pk} angelegt: {name}")
            else:
                logger.debug(f"Info {info.pk}: keine passende Aktion")

            info.evaluated    = True
            info.evaluated_at = now
            info.save(update_fields=["evaluated", "evaluated_at"])
        except Exception as e:
            logger.error(f"Fehler bei Evaluierung von Info {info.pk}: {e}")

    logger.info("evaluate_informations-Task beendet")
"""


@shared_task
def update_information_embedding_task(info_pk, update_fields):
    info = Information.objects.get(pk=info_pk)
    text_for_embedding = " ".join(filter(None, [
        info.title,
        info.context,
        info.information_short,
        info.information_long,
    ]))
    new_emb = generate_embedding(text_for_embedding)
    Information.objects.filter(pk=info_pk).update(embedding=new_emb)
    trigger_clustering()

MODEL_HANDLERS = {
    'my_ai_app.RequiredInformation': create_information_for_required_information,
    'my_ai_app.TextInput': create_information_for_text_input,
}
@shared_task
def handle_information_creation_task(model_label, obj_pk):
    handler = MODEL_HANDLERS.get(model_label)
    if not handler:
        return
    try:
        # handler erwartet das Objekt; wir holen es dynamisch
        app_label, model_name = model_label.split(".")
        ct = ContentType.objects.get(app_label=app_label, model=model_name)
        model = ct.model_class()
        instance = model.objects.get(pk=obj_pk)
        handler(instance)
    except Exception as e:
        logging.getLogger(__name__).error(
            f"Fehler in Information-Erstellung für {model_label}: {e}", exc_info=True
        )