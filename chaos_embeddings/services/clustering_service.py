import logging

import numpy as np
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from sklearn.cluster import DBSCAN

from chaos_embeddings.models import Embedding
from chaos_information.models import Information

logger = logging.getLogger(__name__)

def trigger_clustering(eps: float = 0.5, min_samples: int = 2):
    """
    Cluster alle Information-Embeddings und schreibe die cluster_id
    in das Embedding-Objekt.
    """
    info_ct = ContentType.objects.get_for_model(Information)
    embs = Embedding.objects.filter(content_type=info_ct)
    vectors = np.array([e.vector for e in embs])
    emb_ids = [e.id for e in embs]

    logger.debug(f"[clustering] Starte mit {len(emb_ids)} Embeddings")

    if vectors.size == 0:
        logger.warning("[clustering] Keine Embeddings zum Clustern gefunden.")
        return

    clustering = DBSCAN(eps=eps, min_samples=min_samples, metric='cosine')
    labels = clustering.fit_predict(vectors)

    with transaction.atomic():
        for emb_id, label in zip(emb_ids, labels):
            Embedding.objects.filter(pk=emb_id).update(cluster_id=int(label))

    logger.info(f"[clustering] Clustering abgeschlossen: {len(set(labels))} Cluster")
