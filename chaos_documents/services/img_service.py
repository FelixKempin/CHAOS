import base64
import logging
from io import BytesIO

from openai import OpenAI
from PIL import Image
import pytesseract
from django.conf import settings

logger = logging.getLogger(__name__)
client = OpenAI(api_key=settings.OPENAI_API_KEY)
import base64
import logging
from io import BytesIO
from openai import OpenAI
from PIL import Image

logger = logging.getLogger(__name__)
client = OpenAI(api_key=settings.OPENAI_API_KEY)

def extract_text_from_image(file_field) -> str:
    """
    Analysiert ein Bild per GPT-4o Vision:
     - Erkennt, was auf dem Bild zu sehen ist (Typ, Szene, Objekt).
     - Extrahiert enthaltenen Text (sofern vorhanden).
     - Gibt strukturierte Ausgabe zurück.
     - Verzichtet komplett auf OCR (kein Tesseract).
    """
    try:
        file_field.open("rb")
        img_bytes = file_field.read()
        file_field.close()

        img_b64 = base64.b64encode(img_bytes).decode("utf-8")

        messages = [
            {
                "role": "system",
                "content": (
                    "Du analysierst ein Bild. Gib eine strukturierte Antwort mit:\n"
                    "**Bildtyp**: (z.B. Dokument, Foto, Formular, Screenshot)\n"
                    "**Beschreibung**: (was ist grundsätzlich zu sehen?)\n"
                    "**Text**: (nur, wenn Text sichtbar ist – gib ihn vollständig und unverändert wieder)"
                )
            },
            {
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_b64}"}},
                    {"type": "text", "text": "Analysiere bitte dieses Bild gemäß der Struktur."}
                ]
            }
        ]

        resp = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            max_tokens=2000,
            temperature=0.2,
        )
        text = resp.choices[0].message.content.strip()
        if text:
            logger.debug(f"Bildanalyse via GPT-4o erfolgreich ({len(text)} Zeichen)")
            return text

        logger.warning("GPT-4o lieferte keinen Inhalt zurück.")
        return ""

    except Exception as e:
        logger.exception(f"Fehler bei der Bildanalyse: {e}")
        return ""
