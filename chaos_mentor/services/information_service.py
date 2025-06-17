import json
import logging
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from django.conf import settings
import openai
from chaos_documents.services.pdf_service import extract_text_from_pdf
from chaos_information.services.information_service import create_information
from chaos_documents.services.img_service import extract_text_from_image
from chaos_documents.services.txt_service import extract_text_from_txt


from chaos_documents.services.markdown_service import md_to_text

logger = logging.getLogger("document_agent_app")

def create_information_for_goal(goal):
    logger.debug(f"[create_info_goal] Starte Verarbeitung für Ziel {goal.pk}")

    text_parts = []
    if goal.name is not None:
        text_parts.append(f"{goal.name} \n")
    if goal.definition_description:
        logger.debug(f"[create_info_goal] Goal_Description gefunden ({len(goal.definition_description)} Zeichen), füge hinzu")
        text_parts.append(f"Ziel-Beschreibung: {goal.definition_description} \n")

    text_parts.append(f"Zeitraum: {goal.type} \n")



    full_text = "\n\n".join(text_parts).strip()
    if not full_text:
        logger.error(f"[create_info_pdf] Keine Inhalte für Information bei {goal.pk}, breche ab")
        return None

    logger.debug(f"[create_info_pdf] Gesamtlänge Text: {len(full_text)} Zeichen, erstelle Information…")

    meta_tx = ""
    if goal.meta_description:
        meta_tx = goal.meta_description

    return create_information(goal, meta_tx, full_text)


def create_information_for_goal_status_update(goal_status_update):
    """
    Verarbeitet TEXT_Document:
    - Immer meta_description vorneweg.
    - Dann: wenn File da → extract, sonst reiner meta-Text.
    """
    logger.debug(f"[create_info_text] Starte Verarbeitung für Text-Dokument {goal_status_update}")

    text_parts = []
    if goal_status_update.meta_description:
        logger.debug(f"[create_info_goal_status_update] Meta-Description ({len(goal_status_update.meta_description)} Zeichen), füge hinzu")
        text_parts.append(f"Meta-Description: {goal_status_update.meta_description} \n")
    if goal_status_update.content:
        text_parts.append(f"{goal_status_update.content} \n")


    full_text = "\n\n".join(text_parts).strip()
    if not full_text:
        logger.error(f"[create_info_goal_status_update] Kein Text vorhanden bei {goal_status_update.pk}. Abbruch.")
        raise ValueError("Kein Text übergeben. meta_description oder Datei nötig.")

    logger.debug(f"[create_info_goal_status_update] Gesamtlänge Text: {len(full_text)} Zeichen, rufe create_information…")
    meta_tx = ""
    if goal_status_update.meta_description:
        meta_tx = goal_status_update.meta_description

    return create_information(goal_status_update, meta_tx, full_text)


def create_information_for_advice(advice):
    logger.debug(f"[create_info_img] Starte Verarbeitung für Bild-Dokument {advice.pk}")

    text_parts = []
    if advice.meta_description:
        logger.debug(f"[create_info_advice] Meta-Description ({len(advice.meta_description)} Zeichen), füge hinzu")
        text_parts.append(f"Meta_Description: {advice.meta_description} \n")

    if advice.content:
        text_parts.append(f"{advice.content} \n")



    full_text = "\n\n".join(text_parts).strip()
    if not full_text:
        logger.error(f"[create_info_advice] Keine Inhalte für Information bei {advice.pk}, breche ab")
        return None

    logger.debug(f"[create_info_img] Gesamtlänge Text: {len(full_text)} Zeichen, erstelle Information…")
    meta_tx = ""
    if advice.meta_description:
        meta_tx = advice.meta_description

    return create_information(advice, meta_tx, full_text)
