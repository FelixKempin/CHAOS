import uuid
from django.db import models
from django.contrib.contenttypes.fields import GenericRelation


from . import tasks
from .services.storage_backends import DocumentMediaStorage
from .utils import document_upload_to, markdown_image_upload_to
from chaos_information.models import Information


class Document(models.Model):
    id           = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name         = models.CharField(max_length=100, null=True, blank=True)
    date         = models.DateTimeField(auto_now_add=True)
    meta_description = models.TextField(null=True, blank=True)
    # Reverse‐Relation auf Information (gibt QuerySet mit 0 oder 1 Element)
    information  = GenericRelation(
                       Information,
                       content_type_field='content_type',
                       object_id_field='object_id'
                   )

    class Meta:
        abstract = True

class IMG_Document(Document):
    file             = models.ImageField(upload_to=document_upload_to, storage=DocumentMediaStorage(),blank=True, null=True)


class PDF_Document(Document):
    file             = models.FileField (upload_to=document_upload_to, storage=DocumentMediaStorage(),blank=True, null=True)


class CSV_Document(Document):
    file             = models.FileField (upload_to=document_upload_to,storage=DocumentMediaStorage(), blank=True, null=True)


class TEXT_Document(Document):
    file             = models.FileField (upload_to=document_upload_to, storage=DocumentMediaStorage(), blank=True, null=True)


class MARKDOWN_Document(Document):
    file             = models.FileField (upload_to=document_upload_to,storage=DocumentMediaStorage(), blank=True, null=True)
    # temporäres Feld zum Speichern einzelner Upload-Bilder
    markdown_image = models.ImageField(
        upload_to=markdown_image_upload_to,
        storage=DocumentMediaStorage(),
        blank=True,
        null=True
    )


class AUDIO_Document(Document):
    file             = models.FileField (upload_to=document_upload_to, storage=DocumentMediaStorage(),blank=True, null=True)



