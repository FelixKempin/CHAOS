import logging
import tempfile


logger = logging.getLogger(__name__)

def extract_text_from_txt(file_field) -> str:
    try:
        file_field.open("rb")
        content = file_field.read().decode("utf-8")
        return content.strip()
    except Exception as e:
        logger.error(f"In-Memory TXT-Lesefehler: {e}")
        return ""
