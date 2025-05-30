import uuid
from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from pgvector.django import VectorField, IvfflatIndex

class Embedding(models.Model):
    """
    Generischer Embedding‐Container für beliebige Objekte.
    """
    id             = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    content_type   = models.ForeignKey(ContentType, on_delete=models.CASCADE, db_index=True)
    object_id      = models.CharField(max_length=36, db_index=True)
    content_object = GenericForeignKey('content_type', 'object_id')

    vector     = VectorField(dimensions=1536)
    cluster_id = models.IntegerField(null=True, blank=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        unique_together = ('content_type', 'object_id')
        indexes = [
            IvfflatIndex(
                name='embeddings_vector_ivfflat',
                fields=['vector'],
                lists=100,
                opclasses=['vector_l2_ops']
            ),
        ]
