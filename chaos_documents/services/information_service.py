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

logger = logging.getLogger("document_agent_app")

def create_information_for_pdf_doc(doc):
    logger.debug(f"[create_info_pdf] Starte Verarbeitung für PDF-Dokument {doc.pk}")

    text_parts = []
    if doc.meta_description:
        logger.debug(f"[create_info_pdf] Meta-Description gefunden ({len(doc.meta_description)} Zeichen), füge hinzu")
        text_parts.append(f"User-Text: {doc.meta_description}")

    try:
        extracted = extract_text_from_pdf(doc.file)
        if not extracted.strip():
            logger.warning(f"[create_info_pdf] Kein Text extrahiert bei {doc.pk}")
        else:
            logger.info(f"[create_info_pdf] Text extrahiert ({len(extracted)} Zeichen), füge hinzu")
            text_parts.append(extracted)
    except Exception as e:
        logger.exception(f"[create_info_pdf] Fehler beim Extrahieren von PDF {doc.pk}: {e}")

    full_text = "\n\n".join(text_parts).strip()
    if not full_text:
        logger.error(f"[create_info_pdf] Keine Inhalte für Information bei {doc.pk}, breche ab")
        return None

    logger.debug(f"[create_info_pdf] Gesamtlänge Text: {len(full_text)} Zeichen, erstelle Information…")

    meta_tx = ""
    if doc.meta_description:
        meta_tx = doc.meta_description

    return create_information(doc,meta_tx, full_text)


def create_information_for_text_doc(doc):
    """
    Verarbeitet TEXT_Document:
    - Immer meta_description vorneweg.
    - Dann: wenn File da → extract, sonst reiner meta-Text.
    """
    logger.debug(f"[create_info_text] Starte Verarbeitung für Text-Dokument {doc.pk}")

    text_parts = []
    if doc.meta_description:
        logger.debug(f"[create_info_text] Meta-Description ({len(doc.meta_description)} Zeichen), füge hinzu")
        text_parts.append(f"User-Text: {doc.meta_description}")

    # Extrahiere falls möglich
    if doc.file and getattr(doc.file, 'name', None):
        try:
            extracted = extract_text_from_txt(doc.file)
            if not extracted.strip():
                logger.warning(f"[create_info_text] Extraktion lieferte leeren Text bei {doc.pk}")
            else:
                logger.info(f"[create_info_text] Text extrahiert ({len(extracted)} Zeichen), füge hinzu")
                text_parts.append(extracted)
        except Exception as e:
            logger.error(f"[create_info_text] Fehler beim TXT-Extract für {doc.pk}: {e}")
    else:
        logger.debug(f"[create_info_text] Kein File, benutze nur Meta-Description")

    full_text = "\n\n".join(text_parts).strip()
    if not full_text:
        logger.error(f"[create_info_text] Kein Text vorhanden bei {doc.pk}. Abbruch.")
        raise ValueError("Kein Text übergeben. meta_description oder Datei nötig.")

    logger.debug(f"[create_info_text] Gesamtlänge Text: {len(full_text)} Zeichen, rufe create_information…")
    meta_tx = ""
    if doc.meta_description:
        meta_tx = doc.meta_description

    return create_information(doc, meta_tx, full_text)


def create_information_for_img_doc(doc):
    logger.debug(f"[create_info_img] Starte Verarbeitung für Bild-Dokument {doc.pk}")

    text_parts = []
    if doc.meta_description:
        logger.debug(f"[create_info_img] Meta-Description ({len(doc.meta_description)} Zeichen), füge hinzu")
        text_parts.append(f"User-Text: {doc.meta_description}")

    try:
        extracted = extract_text_from_image(doc.file)
        if not extracted.strip():
            logger.warning(f"[create_info_img] OCR lieferte keinen Text bei {doc.pk}")
        else:
            logger.info(f"[create_info_img] OCR-Text extrahiert ({len(extracted)} Zeichen), füge hinzu")
            text_parts.append(extracted)
    except Exception as e:
        logger.exception(f"[create_info_img] Fehler bei OCR für Bild-Dokument {doc.pk}: {e}")

    full_text = "\n\n".join(text_parts).strip()
    if not full_text:
        logger.error(f"[create_info_img] Keine Inhalte für Information bei {doc.pk}, breche ab")
        return None

    logger.debug(f"[create_info_img] Gesamtlänge Text: {len(full_text)} Zeichen, erstelle Information…")
    meta_tx = ""
    if doc.meta_description:
        meta_tx = doc.meta_description

    return create_information(doc, meta_tx, full_text)
