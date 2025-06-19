from .models import Embedding
from pgvector.django import L2Distance

def get_similar_embeddings(vector, top_k=5):
    return (
        Embedding.objects
        .annotate(distance=L2Distance("vector", vector))
        .order_by("distance")[:top_k]
    )
