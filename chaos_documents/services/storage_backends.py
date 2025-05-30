# document_agent_app/storage_backends.py

from storages.backends.gcloud import GoogleCloudStorage
from django.conf import settings

class DocumentMediaStorage(GoogleCloudStorage):
    def __init__(self, *args, **kwargs):
        kwargs['bucket_name'] = settings.GS_BUCKET_NAME
        kwargs['project_id'] = getattr(settings, 'GS_PROJECT_ID', None)
        kwargs['location'] = settings.GS_LOCATION
        kwargs['credentials'] = getattr(settings, 'GS_CREDENTIALS', None)
        kwargs['default_acl'] = None
        super().__init__(*args, **kwargs)