import uuid

from django.contrib.contenttypes.fields import GenericRelation
from django.db import models

from chaos_information.models import Information


# Create your models here.


class DailyJournal(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    date = models.DateTimeField()
    meta_description = models.TextField(null=True, blank=True)
    information = GenericRelation(
        Information,
        content_type_field='content_type',
        object_id_field='object_id'
    )

    daily_summary = models.TextField(null=True, blank=True)
    positive_things = models.TextField(null=True, blank=True)
    negative_things = models.TextField(null=True, blank=True)
    daily_thoughts = models.TextField(null=True, blank=True)





