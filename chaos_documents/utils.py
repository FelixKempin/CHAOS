import tempfile
from datetime import datetime
import uuid
import os
import logging

logger = logging.getLogger(__name__)

def document_upload_to(instance, filename):
    """
    Bucket-Pfad: YYYY/MM/DD/MODELNAME/uuid.ext
    """
    now = datetime.utcnow()
    ext = os.path.splitext(filename)[1]
    model = instance._meta.model_name.upper()
    name = f"{uuid.uuid4()}{ext}"
    return f"{now.year}/{now.month:02}/{now.day:02}/{model}/{name}"



def get_temp_file_from_django_file(django_file_field, suffix=""):
    """
    Speichert eine Django FileField-Datei temporär lokal ab
    (z. B. für GCS-kompatible Verarbeitung mit OCR/PDF).
    """
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix, mode="wb") as tmp_file:
            for chunk in django_file_field.chunks():
                tmp_file.write(chunk)
            return tmp_file.name
    except Exception as e:
        logger.error(f"Fehler beim Speichern der temporären Datei: {e}")
        raise
