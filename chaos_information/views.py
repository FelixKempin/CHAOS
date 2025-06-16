from django.db.models import Case, When, IntegerField, F, Q
from django.db.models.expressions import RawSQL
from django.views.generic import DetailView
from chaos_embeddings.models import Embedding
from chaos_embeddings.services.embedding_service import generate_embedding
from dal import autocomplete
from django.views.generic import ListView, UpdateView, DeleteView, CreateView, TemplateView
from django.db.models import Q, Count, Subquery, OuterRef
from sklearn.decomposition import PCA
from .models import TextInput,RelevanceEvent
from .forms import InformationFilterForm, InformationForm
from .services.thread_service import chat_with_context
import uuid
from scipy.spatial import distance
from django.views.decorators.http import require_GET, require_POST
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.generic import ListView, View
from django.contrib.contenttypes.models import ContentType
from django.db.models import Subquery, OuterRef, IntegerField
from django.urls import reverse
from .models import Information, Tag, Vault
from .forms import InformationFilterForm
from .models import RelevanceEvent
import numpy as np
from django.core.cache import cache
from django.urls import reverse_lazy
from django.views.generic import UpdateView
from .models import Information, Folder, Tag
from .forms import InformationForm
import os
from django.shortcuts import render, redirect
from chaos_documents.models import (
    PDF_Document, TEXT_Document, CSV_Document,
    MARKDOWN_Document, IMG_Document
)

@require_GET
def search_neighbors(request):
    q = request.GET.get("q", "").strip()
    try:
        threshold = float(request.GET.get("threshold", 1.0))
    except (TypeError, ValueError):
        threshold = 1.0

    if not q:
        return JsonResponse({"info_ids": [], "tag_ids": []})

    query_vec = np.array(generate_embedding(q), dtype=float)

    # Information-Embeddings durchsuchen
    info_ct = ContentType.objects.get_for_model(Information)
    info_qs = Embedding.objects.filter(content_type=info_ct).values_list("object_id", "vector")
    info_ids = [
        obj_id
        for obj_id, vec in info_qs
        if distance.cosine(query_vec, np.array(vec, dtype=float)) <= threshold
    ]

    # Tag-Embeddings durchsuchen
    tag_ct = ContentType.objects.get_for_model(Tag)
    tag_qs = Embedding.objects.filter(content_type=tag_ct).values_list("object_id", "vector")
    tag_ids = [
        obj_id
        for obj_id, vec in tag_qs
        if distance.cosine(query_vec, np.array(vec, dtype=float)) <= threshold
    ]

    # Rückgabe als Strings
    return JsonResponse({
        "info_ids": [str(pk) for pk in info_ids],
        "tag_ids":  [str(pk) for pk in tag_ids],
    })

@require_POST
def update_information_vault(request, pk):
    info = get_object_or_404(Information, pk=pk)
    vault_id = request.POST.get("vault", "").strip()
    if vault_id:
        info.vault = get_object_or_404(Vault, pk=vault_id)
    else:
        info.vault = None
    info.save(update_fields=["vault"])
    return JsonResponse({
        "ok": True,
        "vault": str(info.vault) if info.vault else None
    })

@require_POST
def toggle_status(request, pk):
    info = get_object_or_404(Information, pk=pk)
    new_status = request.POST.get("status")
    if new_status in dict(Information.STATUS_CHOICES):
        info.status = new_status
        info.save(update_fields=["status"])
        badge_class = {
            "pending":   "bg-warning",
            "confirmed": "bg-success",
        }.get(info.status, "bg-secondary")
        return JsonResponse({
            "ok": True,
            "status": info.get_status_display(),
            "badge_class": badge_class
        })
    return JsonResponse({"ok": False}, status=400)

class TagAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        qs = Tag.objects.all()
        if self.q:
            qs = qs.filter(name__icontains=self.q)
        return qs.order_by("name")

class InformationListView(ListView):
    model = Information
    template_name = "information_list.html"
    context_object_name = "infos"
    paginate_by = 10

    def get_queryset(self):
        # Subquery für den letzten RelevanceEvent.score
        last_score = Subquery(
            RelevanceEvent.objects
                .filter(information=OuterRef("pk"))
                .order_by("-timestamp")
                .values("score")[:1],
            output_field=IntegerField(),
        )

        qs = (
            Information.objects
            .only("id", "title", "datetime", "status", "vault_id", "folder_id")
            .select_related("vault", "folder")
            .prefetch_related("tags")
            .annotate(last_score=last_score)
        )

        self.filter_form = InformationFilterForm(self.request.GET or None)

        if self.filter_form.is_valid():
            cd = self.filter_form.cleaned_data

            if cd.get("q"):
                qs = qs.filter(title__icontains=cd["q"])
            if cd.get("text"):
                qs = qs.filter(information_long__icontains=cd["text"])
            if cd.get("tags"):
                qs = qs.filter(tags__in=cd["tags"]).distinct()
            if cd.get("vault"):
                qs = qs.filter(vault=cd["vault"])
            if cd.get("date_from"):
                qs = qs.filter(datetime__date__gte=cd["date_from"])
            if cd.get("date_to"):
                qs = qs.filter(datetime__date__lte=cd["date_to"])
            if cd.get("status"):
                qs = qs.filter(status=cd["status"])
            if cd.get("object_type"):
                qs = qs.filter(object_type_string=cd["object_type"])
            if cd.get("min_relevance") is not None:
                qs = qs.filter(last_score__gte=cd["min_relevance"])

            order = cd.get("order")
        else:
            order = None

        if order == "relevance":
            qs = qs.order_by("-last_score")
        else:
            qs = qs.order_by(order or "-datetime")

        return qs


    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["filter_form"] = self.filter_form

        if self.filter_form.is_valid():
            cd = self.filter_form.cleaned_data
            ctx["selected_tags"]         = cd.get("tags", [])
            ctx["selected_vault"]        = cd.get("vault")
            ctx["selected_object_type"]  = cd.get("object_type")  # neu
        else:
            ctx["selected_tags"]         = []
            ctx["selected_vault"]        = None
            ctx["selected_object_type"]  = None

        ctx["all_vaults"] = Vault.objects.filter(active=True).order_by("name")
        return ctx

@method_decorator(csrf_exempt, name="dispatch")
class TagCreateAjaxView(View):
    """
    Ajax-Endpoint zum Inline-Anlegen neuer Tags.
    """
    def post(self, request, *args, **kwargs):
        name = request.POST.get("name", "").strip()
        if not name:
            return JsonResponse({"error": "Kein Name übergeben"}, status=400)
        tag, created = Tag.objects.get_or_create(name=name)
        return JsonResponse({"pk": tag.pk, "name": tag.name})

class InformationUpdateView(UpdateView):
    model = Information
    form_class = InformationForm
    template_name = "information_form.html"
    success_url = reverse_lazy('information_list')

    def form_valid(self, form):
        response = super().form_valid(form)
        # Tags explizit setzen (ersetzen die aktuelle Auswahl)
        tag_pks = self.request.POST.getlist('tags')
        # Ggf. neue Tags (z.B. mit "new:..." prefix) herausfiltern, falls die im JS noch vorkommen könnten
        valid_pks = [pk for pk in tag_pks if pk.isdigit()]
        self.object.tags.set(valid_pks)
        return response

    def get_related_infos(self):
        cache_key = f"related_infos_{self.object.pk}"
        cached = cache.get(cache_key)
        if cached is not None:
            return cached

        info_ct = ContentType.objects.get_for_model(Information)
        try:
            emb = Embedding.objects.get(
                content_type=info_ct,
                object_id=str(self.object.pk)
            )
        except Embedding.DoesNotExist:
            return []

        own_arr = np.array(emb.vector, dtype=float)

        qs = Embedding.objects.filter(
            content_type=info_ct
        ).exclude(object_id=str(self.object.pk))

        if emb.cluster_id is not None:
            qs = qs.filter(cluster_id=emb.cluster_id)

        data = list(qs.values_list('object_id', 'vector'))
        if not data:
            return []

        ids, vecs = zip(*data)
        mat = np.array(vecs, dtype=float)
        dists = np.linalg.norm(mat - own_arr, axis=1)
        idxs = np.argsort(dists)[:5]
        top_ids = [uuid.UUID(ids[i]) for i in idxs]
        top_dists = [float(dists[i]) for i in idxs]

        infos = Information.objects.in_bulk(top_ids)
        result = [
            {'info': infos.get(pk), 'distance': dist}
            for pk, dist in zip(top_ids, top_dists)
            if infos.get(pk)
        ]

        cache.set(cache_key, result, 300)
        return result

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['folder_tree']        = Folder.objects.filter(parent__isnull=True).prefetch_related('children')
        ctx['selected_folder_pk'] = self.object.folder_id
        ctx['selected_tags']      = self.object.tags.all()
        ctx['related_infos']      = self.get_related_infos()
        return ctx

class InformationDeleteView(DeleteView):
    model = Information
    template_name = "information_confirm_delete.html"
    success_url = reverse_lazy('information_list')

class EmbeddingMapView(TemplateView):
    template_name = "embedding_map.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        # — Informationen —
        info_ct = ContentType.objects.get_for_model(Information)
        info_embs = (
            Embedding.objects
            .filter(content_type=info_ct)
            .annotate(title=F('information__title'))
            .values('object_id', 'title', 'vector')
        )

        # — Tags —
        tag_ct = ContentType.objects.get_for_model(Tag)
        tag_embs = (
            Embedding.objects
            .filter(content_type=tag_ct)
            .annotate(name=F('tag__name'))
            .values('object_id', 'name', 'vector')
        )

        # — PCA über alle Vektoren —
        all_vecs = np.array(
            [e['vector'] for e in info_embs] +
            [e['vector'] for e in tag_embs],
            dtype=float
        )
        coords = PCA(n_components=2).fit_transform(all_vecs)
        info_coords = coords[: len(info_embs)]
        tag_coords  = coords[len(info_embs) :]

        # — Punkte fürs Template —
        ctx['info_points'] = [
            {
                'id':    str(e['object_id']),
                'label': e['title'],
                'x':     float(x),
                'y':     float(y),
                'url':   reverse('information_edit', args=[e['object_id']]),
            }
            for e, (x, y) in zip(info_embs, info_coords)
        ]
        ctx['tag_points'] = [
            {
                'id':    str(e['object_id']),
                'label': e['name'],
                'x':     float(x),
                'y':     float(y),
            }
            for e, (x, y) in zip(tag_embs, tag_coords)
        ]

        return ctx









