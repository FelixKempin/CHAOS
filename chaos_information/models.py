# main_app/models.py

import logging
import uuid
from abc import abstractmethod
from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.contrib.postgres.fields import ArrayField
from django.core.exceptions import ValidationError
#from my_ai_app.action_registry import ACTION_REGISTRY
from chaos_embeddings.models import Embedding  # GenericRelation referenziert dieses Model

logger = logging.getLogger(__name__)


class Agent(models.Model):
    active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.get_agent_type_display()} – {self.name}"


class Action(models.Model):
    STATUS_CHOICES = [
        ('waiting',  'Waiting'),
        ('ready',    'Ready'),
        ('success',  'Success'),
        ('failed',   'Failed'),
        ('rejected', 'Rejected'),
        ('information_needed', 'Information needed'),
    ]

    name           = models.CharField(max_length=100)
    status         = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='waiting', db_index=True
    )
    required_check = models.BooleanField(default=False)
    approved       = models.BooleanField(default=False)
    created_at     = models.DateTimeField(auto_now_add=True, db_index=True)

    prerequisites = models.ManyToManyField(
        'self', blank=True, symmetrical=False, related_name='dependents',
        help_text='Actions, die vor dieser hier erfolgreich laufen müssen'
    )

    class Meta:
        ordering = ['-created_at']

    @abstractmethod
    def execute(self):
        raise NotImplementedError

    @property
    def is_ready(self):
        reqs = self.required_informations.all()
        if reqs and not all(r.status == 'provided' for r in reqs):
            return False
        pres = self.prerequisites.all()
        if pres and not all(a.status == 'success' for a in pres):
            return False
        return True

    def run(self):
        if not self.is_ready:
            self.status = 'waiting'
            self.save(update_fields=['status'])
            return
        self.status = 'ready'
        self.save(update_fields=['status'])
        try:
            self.execute()
            self.status = 'success'
        except Exception:
            self.status = 'failed'
            raise
        finally:
            self.save(update_fields=['status'])

"""
class AgentAction(Action):
    function_name   = models.CharField(max_length=100)
    parameters      = models.JSONField(null=True, blank=True)
    result          = models.JSONField(null=True, blank=True)
    information_id  = models.CharField(max_length=64)

    def execute(self):
        meta = ACTION_REGISTRY.get(self.function_name)
        if not meta:
            raise ValueError(f"Unknown action: {self.function_name}")
        func = meta["func"]
        try:
            output = func(self.information_id)
            self.result = {"status": "success", "output": output}
            self.status = "success"
        except Exception as e:
            logger.exception(f"Error executing {self.function_name}")
            self.result = {"status": "error", "error": str(e)}
            self.status = "failed"
        self.save(update_fields=["status", "result"])
"""

class UserAction(Action):
    user_comment = models.TextField(blank=True)

    def execute(self):
        print(f"Running UserAction {self.pk}")

class Tag(models.Model):
    name        = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    # Embeddings liegen jetzt in embeddings.Embedding
    embeddings = GenericRelation(
        'chaos_embeddings.Embedding',  # statt 'embeddings.Embedding'
        content_type_field='content_type',
        object_id_field='object_id',
        related_query_name='tag'
    )
    def __str__(self):
        return self.name

class Vault(models.Model):
    name        = models.CharField(max_length=100)
    description = models.TextField()
    active      = models.BooleanField(default=True)

    def __str__(self):
        return self.name

class Folder(models.Model):
    name        = models.CharField(max_length=100)
    parent      = models.ForeignKey(
        'self', related_name='children', on_delete=models.CASCADE,
        null=True, blank=True
    )
    vault       = models.ForeignKey(
        Vault, related_name='folders', on_delete=models.CASCADE, db_index=True
    )
    description = models.TextField(blank=True)

    class Meta:
        unique_together = ('vault', 'parent', 'name')
        ordering = ['parent__id', 'name']

    def __str__(self):
        return self.get_full_path()

    def get_full_path(self):
        parts = []
        node = self
        while node:
            parts.insert(0, node.name)
            node = node.parent
        return '/'.join(parts)

class Information(models.Model):
    STATUS_CHOICES = [
        ('pending',   'Zu prüfen'),
        ('confirmed', 'Bestätigt'),
        ('archived',  'Abgelegt'),
    ]

    id                   = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title                = models.CharField(max_length=100)
    datetime             = models.DateTimeField(auto_now_add=True, db_index=True)
    status               = models.CharField(
                             max_length=20, choices=STATUS_CHOICES,
                             default='pending', db_index=True
                           )
    vault                = models.ForeignKey(
                             Vault, on_delete=models.SET_NULL,
                             null=True, blank=True, related_name='informations',
                             db_index=True
                           )
    folder               = models.ForeignKey(
                             Folder, on_delete=models.SET_NULL,
                             null=True, blank=True, related_name='infos'
                           )
    tags                 = models.ManyToManyField('Tag', related_name='informations', blank=True)
    context              = models.TextField(blank=True)
    information_short    = models.TextField(blank=True)
    information_long     = models.TextField(blank=True)
    information_original = models.TextField(blank=True)
    draft                = models.BooleanField(default=False)
    evaluated            = models.BooleanField(default=False)

    content_type         = models.ForeignKey(
                             ContentType, on_delete=models.CASCADE,
                             limit_choices_to={'model__in': (
                                 'img_document', 'pdf_document', 'csv_document',
                                 'text_document', 'markdown_document', 'audio_document',
                                 'contact', 'message', 'todo', 'appointment',
                                 'requiredinformation', 'recurrencerule', 'text_input',
                             )},
                             db_index=True
                           )
    object_id            = models.CharField(max_length=36, db_index=True)
    content_object       = GenericForeignKey('content_type', 'object_id')
    object_type_string   = models.CharField(
                             max_length=50, db_index=True,
                             help_text="Redundanter String des Objekttyps"
                           )

    # Embeddings jetzt in embeddings.Embedding
    embeddings           = GenericRelation(
                             'chaos_embeddings.Embedding',
                             content_type_field='content_type',
                             object_id_field='object_id',
                             related_query_name='information'
                           )

    class Meta:
        unique_together = ('content_type', 'object_id')
        indexes = [
            models.Index(fields=['vault', 'status', 'datetime']),
            models.Index(fields=['content_type', 'object_id']),
            models.Index(fields=['object_type_string']),
        ]
        ordering = ['-datetime']

    def save(self, *args, **kwargs):
        if self.content_type:
            self.object_type_string = self.content_type.model
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.datetime:%Y-%m-%d %H:%M} – {self.title}"

    def get_status_display(self) -> str:
        return dict(self.STATUS_CHOICES).get(self.status, self.status)

class ReviewProposal(models.Model):
    proposed_type = models.CharField(
        max_length=20,
        choices=[('thread','Thread'), ('subject','Subject')]
    )
    name        = models.CharField(max_length=100)
    hierarchy   = models.TextField(help_text='JSON-Array der Thread-Hierarchie')
    source_text = models.TextField(help_text='Auszug des Originaltexts')
    reviewed    = models.BooleanField(default=False)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Review Proposal"
        verbose_name_plural = "Review Proposals"

    def __str__(self):
        return f"Proposal [{self.proposed_type}] {self.name}"

class RelevanceEvent(models.Model):
    information = models.ForeignKey(
        Information, related_name='relevance_events',
        on_delete=models.CASCADE, db_index=True
    )
    score       = models.PositiveSmallIntegerField()
    timestamp   = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-timestamp']

class TextInput(models.Model):
    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    text        = models.TextField()
    date        = models.DateTimeField(auto_now_add=True)
    information = GenericRelation(
                     Information,
                     content_type_field='content_type',
                     object_id_field='object_id'
                  )

class RequiredInformation(models.Model):
    STATUS_CHOICES = [
        ('waiting',  'Waiting'),
        ('provided', 'Provided'),
    ]

    action      = models.ForeignKey(
                     Action, on_delete=models.CASCADE,
                     related_name='required_informations'
                  )
    information = models.ForeignKey(
                     Information, on_delete=models.CASCADE,
                     null=True, blank=True
                  )
    status      = models.CharField(max_length=20, choices=STATUS_CHOICES, default='waiting')
    answer      = models.TextField(blank=True)

    class Meta:
        unique_together = [('action','information')]

# Document‐Models bleiben unverändert…
