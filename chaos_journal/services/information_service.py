import logging
from chaos_information.services.information_service import create_information

logger = logging.getLogger("document_agent_app")

def create_information_for_journal(journal):
    logger.debug(f"[create_info_goal] Starte Verarbeitung für Ziel {journal.pk}")

    text_parts = []
    if journal.name is not None:
        text_parts.append(f"{journal.name} \n")
    if journal.date:
        logger.debug(f"[create_info_goal] date gefunden ({len(journal.definition_description)} Zeichen), füge hinzu")
        text_parts.append(f"Datum: {journal.date} \n")
    if journal.daily_summary:
        text_parts.append(f"{journal.daily_summary} \n")
    if journal.positive_things:
        text_parts.append(f"{journal.positive_things} \n")
    if journal.negative_things:
        text_parts.append(f"{journal.negative_things} \n")
    if journal.daily_thoughts:
        text_parts.append(f"{journal.daily_thoughts} \n")


    full_text = "\n\n".join(text_parts).strip()
    if not full_text:
        logger.error(f"[create_info_journal] Keine Inhalte für Information bei {journal.pk}, breche ab")
        return None

    logger.debug(f"[create_info_journal] Gesamtlänge Text: {len(full_text)} Zeichen, erstelle Information…")

    meta_tx = ""
    if journal.meta_description:
        meta_tx = journal.meta_description

    return create_information(journal, meta_tx, full_text)
