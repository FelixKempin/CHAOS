
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Systempakete installieren (für pdf2image, pytesseract, pillow etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential gcc libpq-dev libjpeg-dev zlib1g-dev \
    poppler-utils tesseract-ocr ghostscript fonts-dejavu-core \
 && apt-get clean && rm -rf /var/lib/apt/lists/*

# Abhängigkeiten installieren
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# App-Code kopieren
COPY . /app/

# Statische Dateien sammeln (optional, falls STATIC_ROOT genutzt wird)
RUN python manage.py collectstatic --noinput || true

# Startbefehl für Gunicorn
CMD ["gunicorn", "CHAOS.wsgi:application", "--bind", "0.0.0.0:8000"]
