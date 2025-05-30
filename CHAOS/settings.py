import atexit
import os
import re
import subprocess
import sys
import base64
import tempfile
from pathlib import Path

import dj_database_url
from celery.schedules import crontab
from dotenv import load_dotenv
from google.oauth2 import service_account

# Load .env
load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

OPEN_AI_MODEL_EMBEDDING = "text-embedding-ada-002"
OPEN_AI_MODEL_CLASSIFY = "gpt-4.1-nano"
OPEN_AI_MODEL_TEXT = "gpt-4.1-mini"
OPEN_AI_MODEL_IMAGE_TO_TEXT = ""

import base64, os, tempfile



_IMAGE_TO_TEXT = ""
import os

ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "").split(",")

# Google Credentials (Base64)
GS_CREDENTIALS = None
raw_b64 = os.getenv("GOOGLE_APPLICATION_CREDENTIALS_JSON_B64", "")
b64 = re.sub(r'\s+', '', raw_b64)

try:
    missing_padding = len(b64) % 4
    if missing_padding:
        b64 += "=" * (4 - missing_padding)

    decoded = base64.b64decode(b64)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".json", mode="wb") as tf:
        tf.write(decoded)
        tf.flush()
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = tf.name
        GS_CREDENTIALS = service_account.Credentials.from_service_account_file(tf.name)
except Exception as e:
    print("⚠️ Failed to decode or load Google credentials:", e)
    GS_CREDENTIALS = None

# OpenAI
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME'),
        'USER': os.getenv('DB_USER'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': os.getenv('DB_HOST'),
        'PORT': os.getenv('DB_PORT', '5432'),
        'CONN_MAX_AGE': 600,
        'OPTIONS': {'sslmode': 'require'},
    }
}


# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'storages',
    'widget_tweaks',
    'dal',
    'dal_select2',
    'pgvector',
    # CHAOS APPS
    'chaos_core',
    'chaos_chat',
    'chaos_documents',
    'chaos_embeddings',
    'chaos_information',
    'chaos_organizer',
    'chaos_assistent',

]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'CHAOS.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [ BASE_DIR / 'templates' ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'CHAOS.wsgi.application'

import os
import dj_database_url

import os




import os



# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',},
]



CELERY_BROKER_URL = os.getenv('REDIS_URL')
CELERY_RESULT_BACKEND = os.getenv('REDIS_URL')
CELERY_TASK_ALWAYS_EAGER = False
CELERY_TASK_EAGER_PROPAGATES = True
CELERY_TASK_DEFAULT_QUEUE = 'celery'  # Explizit hinzufügen


LANGUAGE_CODE = 'de'
TIME_ZONE = 'Europe/Berlin'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
# Ordner, in dem collectstatic alle Files ablegt
STATIC_ROOT = BASE_DIR / 'staticfiles'
#ungesammelten Static-Dateien befinden
STATICFILES_DIRS = [
    BASE_DIR / 'static',    # <projekt-root>/static/css/base_style.css
]

# Für Production mit WhiteNoise
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Bucket-Konfiguration
GS_BUCKET_NAME = os.getenv("GCS_BUCKET") or os.getenv("GCS_BUCKET_NAME")
GS_PROJECT_ID  = os.getenv("GCS_PROJECT_ID")
GOOGLE_APPLICATION_CREDENTIALS = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
# Nur laden, wenn vorher nicht erfolgreich via Base64 gesetzt


GS_LOCATION = "documents"

# Verwende immer GCS als Default-Storage
DEFAULT_FILE_STORAGE = "storages.backends.gcloud.GoogleCloudStorage"

# URL, unter der deine Mediendateien erreichbar sind
MEDIA_URL = f"https://storage.googleapis.com/{GS_BUCKET_NAME}/{GS_LOCATION}/"
# keine lokale Speicherung
MEDIA_ROOT = None

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
# Logging
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "[{asctime}] [{levelname}] {name}: {message}",
            "style": "{",
        },
        "simple": {
            "format": "{levelname}: {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "DEBUG",  # Erhöhe für mehr Details
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "celery": {
            "handlers": ["console"],
            "level": "DEBUG",
            "propagate": False,
        },
        "document_agent_app": {
            "handlers": ["console"],
            "level": "DEBUG",
            "propagate": False,
        },
    },
}

"""
CELERY_BEAT_SCHEDULE = {
    # jede 5 Minuten alle neuen Informationen evaluieren
    'evaluate-informations-every-5-minutes': {
        'task': '',
        'schedule': crontab(minute='*/5'),
    },
    # jede Minute alle AgentActions ausführen
    'process-agent-actions-every-minute': {
        'task': '',
        'schedule': crontab(),  # default: jede Minute
    },
}
"""