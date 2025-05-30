import uuid

from django.db import models


# Create your models here.

TASK_TYPE_REGISTRY = [('')]


# Task Tracking and Retrys
class CHAOS_Task:
    STATUS_CHOICES = [('pending', 'pending'), ('running', 'running'), ('complete', 'complete'), ('failed', 'failed')]


    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    def execute(self):
        pass


    def __str__(self):
        return str(self.id)