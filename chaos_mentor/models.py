import uuid

from django.contrib.contenttypes.fields import GenericRelation
from django.db import models

from chaos_information.models import Information

from chaos_organizer.models import ToDo


# Create your models here.



class Goal(models.Model):
    GOAL_TYPE_CHOICES = [
        ('KURZFRISTIG', 'Kurzfristig'),
        ('MITTELFRISTIG', 'Mittelfristig'),
        ('LANGFRISTIG', 'Langfristig'),
    ]

    type = models.CharField(choices=GOAL_TYPE_CHOICES, max_length=32)
    name = models.TextField(null=True, blank=True)
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    date = models.DateTimeField(auto_now_add=True)
    meta_description = models.TextField(null=True, blank=True)
    information = GenericRelation(
        Information,
        content_type_field='content_type',
        object_id_field='object_id'
    )
    definition_description = models.TextField(null=True, blank=True)
    definition_date = models.DateTimeField(auto_now_add=True)
    definition_conditions = models.TextField(null=True, blank=True)

class GoalStatusUpdate(models.Model):

    goal = models.ForeignKey(Goal, on_delete=models.CASCADE)
    content = models.TextField(null=True, blank=True)
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    date = models.DateTimeField(auto_now_add=True)
    meta_description = models.TextField(null=True, blank=True)
    information = GenericRelation(
        Information,
        content_type_field='content_type',
        object_id_field='object_id'
    )

class Advice(models.Model):
    goal = models.ForeignKey(Goal, on_delete=models.CASCADE)
    title = models.TextField(null=True, blank=True)
    content = models.TextField(null=True, blank=True)
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    date = models.DateTimeField(auto_now_add=True)
    meta_description = models.TextField(null=True, blank=True)
    information = GenericRelation(
        Information,
        content_type_field='content_type',
        object_id_field='object_id'
    )