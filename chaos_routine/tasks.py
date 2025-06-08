from datetime import timedelta
import openai
from django.conf import settings
from django.utils import timezone
from celery import shared_task
from chaos_information.models import Information, RelevanceEvent

client = openai.Client(api_key=settings.OPENAI_API_KEY)

def evaluate_information_actions(info, client):
    """
    Nutzt einen KI-Client, um aus Title und Information_short sinnvolle Aktionen zu bestimmen.
    """
    prompt = f"""Analysiere folgende Information und schlage passende Aktionen vor:
    Titel: {info.title}
    Kurzinfo: {info.information_short}
    
    Antwort-Format: 
    - actions: [string, string, ...]
    - reason: string
    """

    # Beispiel für OpenAI, du kannst auch einen eigenen Client verwenden!
    completion = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "Du bist ein intelligenter Assistent."},
            {"role": "user", "content": prompt}
        ]
    )
    # Extrahiere Actions aus der Antwort
    response = completion.choices[0].message.content
    # Hier solltest du das JSON ggf. parsen (je nach Format)
    # Dummy-Parsing:
    actions = []
    reason = ""
    if "- actions:" in response:
        # (echte Parsing-Logik solltest du je nach Rückgabe einbauen)
        for line in response.split("\n"):
            if line.strip().startswith("- actions:"):
                actions_line = line.split(":", 1)[1]
                actions = [a.strip() for a in actions_line.strip(" []").split(",")]
            if line.strip().startswith("- reason:"):
                reason = line.split(":", 1)[1].strip()
    return actions, reason

def batch_relevance_evaluation(infos, client):
    """
    Schickt mehrere Information-Objekte in einer Anfrage an den Client und erhält ein dict {id: relevance_score}.
    """
    prompt = "Bewerte die Relevanz der folgenden Informationen (0 = irrelevant, 100 = maximal relevant):\n\n"
    for idx, info in enumerate(infos):
        prompt += f"ID: {info.pk}\n Titel: {info.title}\nKurzinfo: {info.information_short}\n\n"
    prompt += "Antworte als JSON-Objekt im Format {id: relevance_score, ...}."

    completion = client.chat.completions.create(
        model=settings.OPEN_AI_MODEL_CLASSIFY,
        messages=[
            {"role": "system", "content": "Du bist ein Assistent, der Relevanzbewertungen macht."},
            {"role": "user", "content": prompt}
        ]
    )
    # Dummy-Parsing (eigene JSON-Logik je nach Rückgabe)
    import json
    response = completion.choices[0].message.content
    try:
        scores = json.loads(response)
    except Exception:
        scores = {}
    return scores  # Dict {id: score}

def calculate_initial_relevance(info):
    # Deine Logik für die Erstbewertung
    if info.object_type_string == "requiredinformation":
        return 5
    if info.object_type_string == "appointment":
        return 4
    if info.object_type_string == "todo":
        return 3
    return 2

def calculate_relevance_score(info):
    # Deine Logik für den Zeitverfall, etc.
    now = timezone.now()
    age_days = (now - info.datetime).days
    base_score = max(1, 5 - age_days // 10)
    return base_score

def perform_initial_actions(info):
    # Hier könntest du Notifications, Assignments, etc. einbauen
    return ["notified_user"]


@shared_task
def rescan_relevance_information():
    now = timezone.now()
    infos = list(
        Information.objects
        .filter(evaluated=True, status__in=['pending', 'confirmed'])
        .filter(
            last_relevance_evaluation__lt=now - timedelta(hours=1)
        )
        .order_by('last_relevance_evaluation')[:10]  # Batchgröße, z.B. 10
    )
    if not infos:
        return "No Information to rescan."

    scores = batch_relevance_evaluation(infos, client)
    updated = 0
    for info in infos:
        new_score = scores.get(str(info.pk))  # IDs als String wegen JSON
        if new_score is not None:
            last_event = info.relevance_events.first()
            if not last_event or abs(new_score - last_event.score) >= 1:
                RelevanceEvent.objects.create(information=info, score=new_score)
                info.relevance_score = new_score
                info.last_relevance_evaluation = now
                info.save(update_fields=["relevance_score", "last_relevance_evaluation"])
            if new_score < 2 and info.status != "archived":
                info.status = "archived"
                info.save(update_fields=["status"])
            updated += 1
    return f"Relevance rescanned for {updated} items."

@shared_task
def evaluate_new_information():
    now = timezone.now()
    info = (
        Information.objects
        .filter(evaluated=False, status__in=['pending', 'confirmed'])
        .order_by('datetime')
        .first()
    )
    if info:
        actions, reason = evaluate_information_actions(info, client)
        #score = calculate_initial_relevance(info)
        info.evaluated = True
        #info.relevance_score = score
        #info.last_relevance_evaluation = now
        #info.save(update_fields=["evaluated", "relevance_score", "last_relevance_evaluation"])
        info.save(update_fields=["evaluated"])
        #RelevanceEvent.objects.create(information=info, score=score)
        # Optionale Speicherung der Aktionen/Begründung (z.B. als Feld/Log/Notification)
        #return f"Evaluated new Information: {info.pk} | Score: {score} | Actions: {actions} | Reason: {reason}"
        return f"Evaluated new Information: {info.pk}  | Actions: {actions} | Reason: {reason}"
    return "No new Information to evaluate."
