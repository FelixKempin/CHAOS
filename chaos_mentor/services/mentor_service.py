import json
import logging

import openai
from django.conf import settings
from google.rpc.status_pb2 import Status

from chaos_mentor.models import Goal, Advice, GoalStatusUpdate

logger = logging.getLogger(__name__)


def openai_evaluate_plan_for_goal(text: str) -> dict:
    prompt = (
            "Du hilfst als Mentor, Ziele zu erreichen. Erstelle konkrete, hilfreiche Anweisungen.\n\n"
            "Gib **ausschließlich** folgendes JSON-Format zurück:\n"
            "{\n"
            '  "title": "Kurze Zusammenfassung des Ziels",\n'
            '  "content": "Detaillierte Schritt-für-Schritt-Anweisung zur Zielerreichung"\n'
            "}\n\n"
            "Achte darauf, dass `content` **ausformulierte Anweisungen** enthält, nicht nur Stichpunkte.\n\n"
            "ZIELBESCHREIBUNG, KONTEXT und STATUS:\n" + text[:4000]
    )

    client = openai.Client(api_key=settings.OPENAI_API_KEY)

    try:
        resp = client.chat.completions.create(
            model=settings.OPEN_AI_MODEL_CLASSIFY,
            messages=[
                {"role": "system", "content": "Hilf als Mentor ein Ziel zu erreichen, antworte **nur mit JSON**."},
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
            "anweisungen",
        ]

        for field in required_fields:
            if field not in parsed or parsed[field] is None:
                logger.warning(f"⚠️ Feld '{field}' fehlt oder ist null – setze Fallback")

        return parsed

    except Exception as e:
        logger.error(f"❌ OpenAI-Feldextraktion fehlgeschlagen: {e}")

def evaluate_goal(goal_pk):
    goal = Goal.objects.get(pk=goal_pk)
    goal_tx = []

    advices = Advice.objects.filter(goal=goal)
    status_updates = GoalStatusUpdate.objects.filter(goal=goal)

    if goal.type:
        goal_tx.append(f"Zeitrahmen: {goal.type} \n")
    if goal.definition_description:
        goal_tx.append(f"Beschreibung: {goal.definition_description} \n")
    if goal.definition_conditions:
        goal_tx.append(f"Bedingungen: {goal.definition_conditions} \n")
    if goal.definition_date:
        goal_tx.append(f"Datum: {goal.definition_date} \n")

    if advices:
        for advice in advices:
            goal_tx.append(f"Bestehende Anweisungen: {advice.title} \n")
    if status_updates:
        for status_update in status_updates:
            goal_tx.append(f"Ziel Historie: {status_update.content} \n")

    full_text = "\n\n".join(goal_tx).strip()
    if not full_text:
        logger.error(f"[create_info_goal_status_update] Kein Text vorhanden bei {goal.pk}. Abbruch.")
        raise ValueError("Kein Text übergeben. meta_description oder Datei nötig.")

    response = openai_evaluate_plan_for_goal(full_text)

    advice = Advice.objects.create(
        title=response["title"],
        content=response["content"],
        goal=goal
    )
    advice.save()


