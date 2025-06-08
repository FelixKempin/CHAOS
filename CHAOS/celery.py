import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'CHAOS.settings')
app = Celery('CHAOS')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks([
    'chaos_chat',
    'chaos_documents',
    'chaos_information',
    'chaos_embeddings',
    'chaos_core',
    'chaos_routine'
])

