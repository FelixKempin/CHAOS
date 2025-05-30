import logging, base64
from io import BytesIO
import PyPDF2, pytesseract
from pdf2image import convert_from_bytes
from PIL import Image
from openai import OpenAI
from django.conf import settings

logger = logging.getLogger("document_agent_app")
client = OpenAI(api_key=settings.OPENAI_API_KEY)

def correct_ocr_with_gpt(text: str) -> str:
    if not text.strip():
        return ""
    try:
        resp = client.chat.completions.create(
            model=settings.OPEN_AI_MODEL_CLASSIFY,
            messages=[
                {"role":"system","content":(
                    "Korrigiere folgenden gescannten Text aus einem Dokument: "
                    "Entferne fehlerhafte Zeichen, korrigiere falsch erkannte Wörter "
                    "und achte auf korrekte Groß-/Kleinschreibung."
                )},
                {"role":"user","content":text},
            ],
            temperature=0.1,
            max_tokens=4000,
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        logger.warning(f"⚠️ GPT-Korrektur fehlgeschlagen: {e}")
        return text

def extract_text_from_pdf(file_field) -> str:
    # 1) Datei einlesen
    try:
        file_field.open("rb")
        pdf_bytes = file_field.read()
        file_field.close()
    except Exception as e:
        logger.error(f"❌ Fehler beim Lesen der Datei: {e}")
        return ""

    text_chunks = []

    # 2) PyPDF2 (Text-Ebene)
    try:
        reader = PyPDF2.PdfReader(BytesIO(pdf_bytes))
        raw = "\n".join(page.extract_text() or "" for page in reader.pages[:5]).strip()
        if raw:
            logger.info("✅ PyPDF2-Text erfolgreich extrahiert")
            text_chunks.append(raw)
        else:
            logger.info("ℹ️ Kein Text aus PyPDF2")
    except Exception as e:
        logger.warning(f"⚠️ PyPDF2-Fehler: {e}")

    # 3) Bilder rendern mit pdf2image
    images = []
    try:
        images = convert_from_bytes(pdf_bytes, dpi=200, first_page=1, last_page=5)
        logger.info("✅ pdf2image-Rendering erfolgreich")
    except Exception as e:
        logger.error(f"❌ pdf2image-Rendering fehlgeschlagen: {e}")

    # 4) Tesseract-OCR
    ocr_results = []
    for idx, img in enumerate(images, start=1):
        try:
            text = pytesseract.image_to_string(img).strip()
            if text:
                logger.info(f"✅ Tesseract Seite {idx}: {len(text)} Zeichen")
                ocr_results.append(text)
            else:
                logger.debug(f"ℹ️ Tesseract Seite {idx} leer")
        except Exception as e:
            logger.warning(f"⚠️ Tesseract-Fehler auf Seite {idx}: {e}")

    if ocr_results:
        combined = "\n".join(ocr_results)
        corrected = correct_ocr_with_gpt(combined)
        text_chunks.append(corrected)

    # 5) GPT-4o Vision als letzter Fallback
    if not text_chunks and images:
        logger.info("ℹ️ Alle OCR-Versuche leer – nutze GPT-4o Vision")
        messages = [{
            "role": "system",
            "content": (
                "Du erhältst gescannte Seiten eines Dokuments als Bild. "
                "Gib bitte den gesamten lesbaren Text exakt zurück."
            )
        }]
        for idx, img in enumerate(images, start=1):
            buffer = BytesIO()
            img.save(buffer, format="PNG")
            img_b64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
            messages.append({
                "role": "user",
                "content": [
                    {"type":"image_url", "image_url":{"url":f"data:image/png;base64,{img_b64}"}},
                    {"type":"text", "text":f"Seite {idx}: bitte den Text extrahieren"}
                ]
            })

        try:
            resp = client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                max_tokens=4000,
                temperature=0.2,
                timeout=60,
            )
            vision_text = resp.choices[0].message.content.strip()
            if vision_text:
                logger.info("✅ GPT-4o Vision erfolgreich")
                text_chunks.append(vision_text)
            else:
                logger.warning("⚠️ GPT-4o Vision lieferte keinen Text")
        except Exception as e:
            logger.error(f"❌ GPT-4o Vision-Fehler: {e}")

    result = "\n\n".join(text_chunks).strip()
    if not result:
        logger.error("❌ Insgesamt kein Text extrahiert")
    return result
