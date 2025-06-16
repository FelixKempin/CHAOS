## chaos_documents/models.py
import re
import uuid
from urllib.parse import urlparse, unquote
from django.db import models, transaction
from django.contrib.contenttypes.fields import GenericRelation
from .services.storage_backends import DocumentMediaStorage
from chaos_information.models import Information
from .utils import document_upload_to, markdown_image_upload_to


class Document(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, null=True, blank=True)
    date = models.DateTimeField(auto_now_add=True)
    meta_description = models.TextField(null=True, blank=True)
    information = GenericRelation(
        Information,
        content_type_field='content_type',
        object_id_field='object_id'
    )

    class Meta:
        abstract = True




class IMG_Document(Document):
    file = models.ImageField(upload_to=document_upload_to,
                              storage=DocumentMediaStorage(),
                              blank=True, null=True)


class PDF_Document(Document):
    file = models.FileField(upload_to=document_upload_to,
                             storage=DocumentMediaStorage(),
                             blank=True, null=True)


class CSV_Document(Document):
    file = models.FileField(upload_to=document_upload_to,
                             storage=DocumentMediaStorage(),
                             blank=True, null=True)


class TEXT_Document(Document):
    file = models.FileField(upload_to=document_upload_to,
                             storage=DocumentMediaStorage(),
                             blank=True, null=True)



class EmbeddedAsset(models.Model):
    object_name = models.CharField(max_length=2048, help_text="GCS object path")

    file = models.FileField(
        upload_to=document_upload_to,
        storage=DocumentMediaStorage(),
        blank=True,
        null=True
    )

    def delete(self, *args, **kwargs):
        self.delete_from_storage()
        super().delete(*args, **kwargs)

    def delete_from_storage(self):
        if self.file:
            try:
                self.file.delete(save=False)
            except Exception:
                pass

    def __str__(self):
        return self.file.url if self.file else self.object_name


class MARKDOWN_Document(Document):
    """
    Ein Markdown-Dokument mit beliebig vielen EmbeddedAssets.
    """
    file = models.FileField(
        upload_to=document_upload_to,
        storage=DocumentMediaStorage(),
        blank=True, null=True
    )
    embedded_assets = models.ManyToManyField(EmbeddedAsset, blank=True)

    def parse_and_attach_assets(self):
        if not self.file:
            return

        raw = self.file.read().decode('utf-8')  # direkt `read()` statt `open().read()`

        # Suche nach GCS-Bild-URLs in Markdown (z. B. ![Alt](https://storage.googleapis.com/bucket/o/xxx))
        link_pattern = re.compile(r'!\[.*?\]\((https?://[^)]+)\)')
        urls = {
            m.group(1)
            for m in link_pattern.finditer(raw)
            if 'storage.googleapis.com' in m.group(1)
        }

        current_obj_names = {
            unquote(urlparse(url).path.split('/o/')[-1])
            for url in urls
        }

        existing_assets = {a.object_name: a for a in self.embedded_assets.all()}

        # Entferne Assets, die nicht mehr im Markdown verwendet werden
        for obj_name, asset in existing_assets.items():
            if obj_name not in current_obj_names:
                asset.delete()
                self.embedded_assets.remove(asset)

        # Neue Assets anlegen
        for url in urls:
            parsed = urlparse(url)
            obj_name = unquote(parsed.path.split('/o/')[-1])

            if obj_name not in existing_assets:
                asset = EmbeddedAsset(object_name=obj_name)
                asset.file.name = obj_name  # Achtung: Datei wird nicht hochgeladen, nur referenziert!
                asset.save()
                self.embedded_assets.add(asset)

    def delete(self, *args, **kwargs):
        for asset in self.embedded_assets.all():
            asset.delete()
        super().delete(*args, **kwargs)

    def save(self, *args, **kwargs):
        is_update = bool(self.pk)
        old_raw = None

        if is_update:
            try:
                old = type(self).objects.get(pk=self.pk)
                if old.file:
                    old_raw = old.file.open('rb').read().decode('utf-8')
            except type(self).DoesNotExist:
                pass

        super().save(*args, **kwargs)

        new_raw = None
        if self.file:
            new_raw = self.file.open('rb').read().decode('utf-8')

        if not is_update or old_raw != new_raw:
            self.parse_and_attach_assets()

class AUDIO_Document(Document):
    file = models.FileField(upload_to=document_upload_to,
                             storage=DocumentMediaStorage(),
                             blank=True, null=True)
