# my_ai_app/services/tag_service.py

import logging
import json

import numpy as np
from scipy.spatial.distance import cosine
from django.contrib.contenttypes.models import ContentType

from openai import OpenAI
from django.conf import settings

from chaos_embeddings.services.embedding_service import generate_embedding
from chaos_information.models import Tag
from chaos_embeddings.models import Embedding

logger = logging.getLogger(__name__)
client = OpenAI(api_key=settings.OPENAI_API_KEY)

MIN_TAGS = 6
MAX_TAGS = 8

def generate_tag_description(name: str) -> str:
    prompt = f"Bitte gib mir eine kurze, prägnante deutsche Beschreibung für den technischen Begriff '{name}'. Antworte nur mit dem Beschreibungstext."
    try:
        resp = client.chat.completions.create(
            model=settings.OPEN_AI_MODEL_CLASSIFY,
            messages=[
                {"role": "system", "content": "Antworte nur mit dem Beschreibungstext."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.0,
            max_tokens=60
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"[GPT] Fehler beim Generieren der Beschreibung für '{name}': {e}")
        return ""

def clean_tag_list(raw_tags: list[str]) -> list[str]:
    seen = set()
    cleaned = []
    for tag in raw_tags:
        tag = tag.strip().capitalize()
        if tag and len(tag) > 2 and tag not in seen:
            seen.add(tag)
            cleaned.append(tag)
    return cleaned

def ask_gpt_for_tags(text: str, max_tags: int) -> list[str]:
    prompt = (
        f"Analysiere den folgenden Text und schlage bis zu {max_tags} präzise und direkt zutreffende Tags vor. "
        f"Vermeide allgemeinere Tags, die nicht im Text vorkommen. "
        f"Nutze Begriffe aus dem Text selbst (wie Orte, Institutionen, Dokumenttypen, Fachrichtungen, Personenrollen, Zeitangaben). "
        f"Antwort nur mit einer JSON-Liste.\n\n"
        f"TEXT:\n{text}"
    )

    try:
        resp = client.chat.completions.create(
            model=settings.OPEN_AI_MODEL_CLASSIFY,
            messages=[
                {"role": "system", "content": "Antworte nur mit einer JSON-Liste."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=150
        )
        raw_output = resp.choices[0].message.content.strip()
        logger.debug(f"[GPT] Rohantwort: {raw_output}")
        return clean_tag_list(json.loads(raw_output))
    except Exception as e:
        logger.error(f"[GPT] Fehler bei ask_gpt_for_tags: {e}")
        return []


def assign_or_create_tags(text: str) -> list[Tag]:
    doc_emb = generate_embedding(text)
    tag_ct = ContentType.objects.get_for_model(Tag)
    distances = []

    # Embedding-Abstand zu existierenden Tags berechnen
    for tag in Tag.objects.all():
        try:
            emb = Embedding.objects.get(content_type=tag_ct, object_id=str(tag.pk))
            distance = cosine(doc_emb, emb.vector)
            distances.append((distance, tag))
        except Embedding.DoesNotExist:
            continue

    distances.sort(key=lambda x: x[0])
    dists_only = [d for d, _ in distances]

    # Dynamische Schwellenwerte
    very_close = float(np.percentile(dists_only, 10)) if dists_only else 0.2
    close_enough = float(np.percentile(dists_only, 25)) if dists_only else 0.4

    selected = [tag for dist, tag in distances if dist < very_close][:MAX_TAGS]
    for dist, tag in distances:
        if len(selected) < MIN_TAGS and very_close <= dist < close_enough and tag not in selected:
            selected.append(tag)

    if len(selected) < MIN_TAGS:
        needed = MIN_TAGS - len(selected)
        try:
            raw_tags = ask_gpt_for_tags(text, needed + 4)  # +4 als Puffer

            # Ähnlichkeit zwischen Tag und Originaltext bewerten
            def score_tag_relevance(tag: str, text: str) -> float:
                tag_emb = generate_embedding(tag)
                return 1.0 - cosine(tag_emb, doc_emb)

            ranked_tags = sorted(
                raw_tags,
                key=lambda tag: score_tag_relevance(tag, text),
                reverse=True
            )

            for name in ranked_tags:
                if len(selected) >= MAX_TAGS:
                    break
                tag, created = Tag.objects.get_or_create(name=name)
                if created:
                    tag.description = generate_tag_description(tag.name)
                    tag.save()
                Embedding.objects.update_or_create(
                    content_type=tag_ct,
                    object_id=str(tag.pk),
                    defaults={'vector': generate_embedding(name)}
                )
                selected.append(tag)
        except Exception as e:
            logger.warning(f"GPT-Taggen fehlgeschlagen: {e}")

    final_selection = selected[:MAX_TAGS]
    logger.info(f"[TAGGING] Ausgewählte Tags: {[t.name for t in final_selection]}")
    return final_selection
