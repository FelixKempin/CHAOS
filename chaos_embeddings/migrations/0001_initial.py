# chaos_embeddings/migrations/0001_initial.py

import uuid
from django.db import migrations, models
from pgvector.django import VectorExtension, VectorField, IvfflatIndex
from django.contrib.postgres.operations import TrigramExtension, BtreeGinExtension
from django.contrib.contenttypes.models import ContentType

class Migration(migrations.Migration):
    initial = True
    dependencies = []
    operations = [
        # 1) Extensions in der DB anlegen
        VectorExtension(),     # CREATE EXTENSION IF NOT EXISTS vector;
        TrigramExtension(),    # CREATE EXTENSION IF NOT EXISTS pg_trgm;
        BtreeGinExtension(),   # CREATE EXTENSION IF NOT EXISTS btree_gin;

        # 2) Dann das Embedding-Modell
        migrations.CreateModel(
            name='Embedding',
            fields=[
                ('id', models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)),
                ('object_id', models.CharField(max_length=36, db_index=True)),
                ('vector', VectorField(dimensions=1536)),
                ('cluster_id', models.IntegerField(null=True, blank=True, db_index=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('content_type', models.ForeignKey(
                    to='contenttypes.ContentType',
                    on_delete=models.CASCADE,
                    db_index=True
                )),
            ],
            options={
                'unique_together': {('content_type', 'object_id')},
                'indexes': [
                    IvfflatIndex(
                        name='embeddings_vector_ivfflat',
                        fields=['vector'],
                        lists=100,
                        opclasses=['vector_l2_ops']
                    ),
                ],
            },
        ),
    ]
