import logging
import json

import openai
from django.conf import settings
from django.db import transaction
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType

from chaos_embeddings.models import Embedding
from chaos_embeddings.services.clustering_service import trigger_clustering
from chaos_embeddings.services.embedding_service import generate_embedding
from chaos_information.models import Information, RelevanceEvent
from chaos_information.services.tag_service import assign_or_create_tags

logger = logging.getLogger(__name__)

def derive_title(text: str) -> str:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return lines[0][:120] if lines else "Ohne Titel"

def openai_parse_information_fields(text: str) -> dict:
    prompt = (
        "Analysiere folgenden Text und extrahiere strukturierte Informationen als JSON.\n"
        "Felder: title, context, information_short, information_long, information_original, relevance (0-100).\n"
        "Antworte mit **gültigem JSON** mit genau diesen Feldern.\n\nTEXT:\n" + text[:4000]
    )

    client = openai.Client(api_key=settings.OPENAI_API_KEY)

    try:
        resp = client.chat.completions.create(
            model=settings.OPEN_AI_MODEL_CLASSIFY,
            messages=[
                {"role": "system", "content": "Extrahiere strukturierte Felder aus dem Text, antworte **nur mit JSON**."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            max_tokens=8000,
        )

        raw = resp.choices[0].message.content.strip()
        cleaned = raw.lstrip("```json").rstrip("```").strip()

        parsed = json.loads(cleaned)

        # Fallbacks setzen, wenn Felder fehlen
        required_fields = [
            "title",
            "context",
            "information_short",
            "information_long",
            "information_original",
            "relevance"
        ]

        for field in required_fields:
            if field not in parsed or parsed[field] is None:
                logger.warning(f"⚠️ Feld '{field}' fehlt oder ist null – setze Fallback")
                if field == "relevance":
                    parsed[field] = 25
                else:
                    parsed[field] = text[:400] if field.startswith("information") else "Ohne Titel"

        return parsed

    except Exception as e:
        logger.error(f"❌ OpenAI-Feldextraktion fehlgeschlagen: {e}")
        return {
            "title": "Ohne Titel",
            "context": text[:200],
            "information_short": text[:500],
            "information_long": text,
            "information_original": text,
            "relevance": 25
        }

def create_information(obj, meta_text: str, text: str = None) -> Information:
    """
    Extrahiere strukturierte Felder, speichere Information und Embedding.
    Das Information-Objekt wird einmal pro Quelldokument angelegt und danach aktualisiert.
    """
    # Legacy-Support für meta_text
    if text is None:
        text, meta_text = meta_text, ""

    # 1) Felder mit OpenAI extrahieren
    parsed = openai_parse_information_fields((meta_text + "\n" + text).strip())

    defaults = {
        'title': parsed['title'],
        'context': parsed['context'],
        'information_short': parsed['information_short'],
        'information_long': parsed['information_long'],
        'information_original': parsed['information_original'],
        'datetime': timezone.now(),
    }

    # 2) Information für das Quellobjekt anlegen oder updaten
    ct_obj = ContentType.objects.get_for_model(obj)
    lookup = {'content_type': ct_obj, 'object_id': str(obj.pk)}

    with transaction.atomic():
        info, created = Information.objects.update_or_create(
            defaults=defaults,
            **lookup
        )

        # 3) Tags zuordnen
        try:
            tags = assign_or_create_tags(text)
            info.tags.set(tags)
        except Exception:
            logger.exception('Fehler bei Tag-Zuordnung')

        # 4) RelevanceEvent erneuern
        try:
            rel_score = int(parsed.get('relevance', 25))
        except (TypeError, ValueError):
            rel_score = 25
        RelevanceEvent.objects.filter(information=info).delete()
        RelevanceEvent.objects.create(score=rel_score, information=info)

        # 5) Embedding für das Information-Objekt anlegen
        try:
            emb_input = "\n".join([
                parsed['title'],
                parsed['context'],
                parsed['information_short'],
                parsed['information_long'],
            ])
            vector = generate_embedding(emb_input)
            ct_info = ContentType.objects.get_for_model(Information)
            Embedding.objects.update_or_create(
                content_type=ct_info,
                object_id=str(info.pk),
                defaults={'vector': vector}
            )
        except Exception:
            logger.exception('Fehler bei Information-Embedding')

    # 6) Clustering asynchron triggern
    trigger_clustering()

    logger.info(f"Information {'erstellt' if created else 'aktualisiert'} (ID={info.pk})")
    return info

def create_information_for_required_information(req_info):
    """
    Erstelle Information für ein RequiredInformation-Objekt.
    """
    from django.utils import timezone
    obj = req_info
    info = Information.objects.create(
        title="Auto-Info",
        context=f"Auto-generated for req {obj.pk}",
        information_short="",
        information_long="",
        information_original="",
        datetime=timezone.now(),
        content_type=ContentType.objects.get_for_model(obj),
        object_id=str(obj.pk),
    )
    # Embedding
    vector = generate_embedding(info.information_long)
    Embedding.objects.create(
        content_type=ContentType.objects.get_for_model(info),
        object_id=str(info.pk),
        vector=vector
    )
    trigger_clustering()
    return info

def create_information_for_text_input(text_input_obj):
    """
    Wrapper: TextInput → Information
    """
    return create_information(text_input_obj, text_input_obj.text)
