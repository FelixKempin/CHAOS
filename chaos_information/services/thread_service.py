import openai
import logging
import numpy as np

from django.conf import settings
from ..models import Information

logger = logging.getLogger(__name__)

# OpenAI-Client initialisieren
client = openai.Client(api_key=settings.OPENAI_API_KEY)

# Schwellen für Detailtiefe
THRESHOLD_ORIGINAL = 0.75
THRESHOLD_LONG = 0.5
MAX_EXCERPT = 300  # Zeichenlimit pro Info


def _get_top_k_infos(embedding: np.ndarray, k: int):
    """Hole top-K Information-Objekte mit ihren Scores."""
    records = Information.objects.exclude(embeddings__isnull=True).values(
        "title", "information_short", "information_long", "information_original", "embeddings__vector"
    )
    scored = []
    for rec in records:
        vec = np.array(rec.pop("embeddings__vector"), dtype=float)
        # Cosine similarity
        denom = (np.linalg.norm(embedding) * np.linalg.norm(vec)) + 1e-8
        score = float(np.dot(embedding, vec) / denom)
        scored.append((score, rec))
    scored.sort(key=lambda x: x[0], reverse=True)
    return scored[:k]


def _format_infos(scored_infos):
    """
    Wähle für jede Info je nach Score Original, Long oder Short,
    und kürze auf MAX_EXCERPT Zeichen.
    """
    lines = []
    for score, info in scored_infos:
        if score >= THRESHOLD_ORIGINAL and info.get("information_original"):
            content = info["information_original"]
        elif score >= THRESHOLD_LONG and info.get("information_long"):
            content = info["information_long"]
        else:
            content = info["information_short"]
        excerpt = content if len(content) <= MAX_EXCERPT else content[:MAX_EXCERPT] + "..."
        lines.append(f"- {info['title']}: {excerpt}")
    return lines


def recursive_retrieval(
    emb_array: np.ndarray,
    k: int,
    depth: int,
    max_depth: int,
    visited: set[str]
) -> list[tuple[float, dict]]:
    """
    Rekursives Holen von Top-k-Informationen bis zur Tiefe max_depth.
    emb_array: aktueller Embedding-Vektor
    k: Anzahl der Nachbarn pro Ebene
    depth: aktuelle Tiefe (0 beim ersten Aufruf)
    visited: Set aus bereits gesehene Information-IDs
    """
    if depth >= max_depth:
        return []

    scored = _get_top_k_infos(emb_array.tolist(), k)
    result = []
    for score, info in scored:
        info_id = info.get("id") or info.get("pk")
        if info_id in visited:
            continue
        visited.add(info_id)
        result.append((score, info))

        # hole das Embedding der gerade gewählten Info
        # (setzen voraus, dass _get_top_k_infos das Feld 'embeddings__vector' liefert)
        vec = np.array(info["embeddings__vector"], dtype=float)
        deeper = recursive_retrieval(
            emb_array=vec,
            k=k,
            depth=depth+1,
            max_depth=max_depth,
            visited=visited
        )
        result.extend(deeper)

    return result

def chat_with_context(
    text: str,
    context_embedding,       # list[float] oder np.ndarray oder None
    context_text: str = "",
    model: str = settings.OPEN_AI_MODEL_TEXT,
    base_k: int = 5
) -> str:
    """
    Baut bei jedem Turn das System-Prompt neu zusammen:
      - k und max_depth je nach Textlänge
      - Retrieval nur, wenn context_embedding != None und k > 0
      - sichere Prüfung auf context_embedding ohne Truth-Ambiguität
    """
    # 0) Kontext-Embedding als numpy array
    emb_array = None
    if context_embedding is not None:
        try:
            emb_array = np.array(context_embedding, dtype=float)
        except Exception as e:
            logger.error(f"Fehler beim Konvertieren des Embeddings: {e}")
            emb_array = None

    # 1) Parameter wählen (k, max_depth) nach Wortzahl
    wc = len(text.split())
    if wc <= 10:
        k, max_depth = 1, 0
    elif wc <= 30:
        k, max_depth = min(3, base_k), 1
    else:
        k, max_depth = base_k, 2

    # 2) Frisches Retrieval
    scored = []
    if emb_array is not None and k > 0:
        visited = set()
        scored = recursive_retrieval(
            emb_array = emb_array,
            k = k,
            depth = 0,
            max_depth = max_depth,
            visited = visited,)
    # 3) System-Prompt aufbauen
    parts = ["Du bist ein hilfreicher Assistent."]
    if context_text:
        snippet = context_text if len(context_text) <= MAX_EXCERPT else context_text[:MAX_EXCERPT] + "..."
        parts.append(f"Subjekt-Kontext:\n{snippet}")

    if scored:
        parts.append("Relevante Informationen:")
        parts.extend(_format_infos(scored))

    system_prompt = "\n\n".join(parts)
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user",   "content": text}
    ]

    # 4) Anfrage an OpenAI (ggf. rekursiv)
    try:
        # Rekursiv nur bei max_depth > 0
        for depth in range(max_depth):
            resp = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.2,
            )
            answer = resp.choices[0].message.content.strip()

            # Nur wenn Depth > 0 und Schlüsselwort auftaucht, Retrieval wiederholen
            if depth < max_depth - 1 and "weitere details" in answer.lower():
                # Retrieval mit tieferen Info-Extrakten
                if emb_array is not None:
                    scored = _get_top_k_infos(emb_array, k)
                deeper = ["Du bist ein hilfreicher Assistent."]
                if context_text:
                    deeper.append(f"Subjekt-Kontext:\n{snippet}")
                deeper.append("Weitergehender Kontext:")
                deeper.extend(_format_infos(scored))
                messages[0]["content"] = "\n\n".join(deeper)
                messages[1]["content"] = text
                continue

            return answer

        # Einfacher Call, wenn keine Rekursion nötig oder Schleife durch
        resp = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.2,
        )
        return resp.choices[0].message.content.strip()

    except Exception as e:
        logger.error(f"Fehler im ChatWithContext: {e}", exc_info=True)
        return "Entschuldigung, da ist etwas schiefgelaufen."
