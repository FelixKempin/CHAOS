# chaos_documents/views.py
from urllib.parse import unquote, urlparse

from django.shortcuts import get_object_or_404
from django.views.generic import ListView, DetailView, CreateView, UpdateView, View, DeleteView
from django.urls import reverse_lazy, reverse
from django.http import JsonResponse
from django.core.files.base import ContentFile
from .models import MARKDOWN_Document, EmbeddedAsset
from .forms import MarkdownDocumentForm
from .services.storage_backends import DocumentMediaStorage


class MarkdownDocumentListView(ListView):
    model = MARKDOWN_Document
    template_name = 'markdown_document_list.html'
    context_object_name = 'markdown_docs'
    paginate_by = 20

class MarkdownDocumentDetailView(DetailView):
    model = MARKDOWN_Document
    template_name = 'markdown_document_detail.html'
    context_object_name = 'markdown_doc'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['embedded_assets'] = self.object.embedded_assets.all()
        return ctx


class MarkdownDocumentCreateView(CreateView):
    model = MARKDOWN_Document
    form_class = MarkdownDocumentForm
    template_name = 'markdown_document_form.html'
    success_url = reverse_lazy('markdown_document_list')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        # neu: kein Objekt, also kein Upload-URL
        ctx['initial_markdown'] = ''
        ctx['upload_url'] = ''
        return ctx

    def form_valid(self, form):
        # wie gehabt: Save, dann Markdown-Datei anlegen
        self.object = form.save(commit=False)
        self.object.save()
        content = self.request.POST.get('file_content', '')
        self.object.file.save(
            f'{self.object.pk}.md',
            ContentFile(content.encode('utf-8')),
            save=True
        )
        return super().form_valid(form)

class MarkdownDocumentUpdateView(UpdateView):
    model = MARKDOWN_Document
    form_class = MarkdownDocumentForm
    template_name = 'markdown_document_form.html'
    success_url = reverse_lazy('markdown_document_list')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        # initialer Datei-Inhalt laden
        data = ''
        if self.object.file:
            data = self.object.file.open('rb').read().decode('utf-8')
        ctx['initial_markdown'] = data

        # Upload-URL
        ctx['upload_url'] = reverse('md_image_upload', kwargs={'pk': self.object.pk})

        # Embedded Assets hinzufügen
        ctx['embedded_assets'] = self.object.embedded_assets.all()

        return ctx

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.save()

        content = self.request.POST.get('file_content', '')
        self.object.file.save(
            f'{self.object.pk}.md',
            ContentFile(content.encode('utf-8')),
            save=True
        )

        # Optional: Nach jedem Speichern Assets aus dem Markdown-Text neu parsen
        # (falls manuelle Links etc. enthalten sind)
        self.object.parse_and_attach_assets()

        return super().form_valid(form)

class MarkdownImageUploadView(View):
    """
    Speichert Drag&Drop-Uploads direkt als EmbeddedAsset.
    """
    def post(self, request, pk):
        doc = get_object_or_404(MARKDOWN_Document, pk=pk)
        upload = request.FILES.get('file')
        if not upload:
            return JsonResponse({'error': 'Kein File'}, status=400)

        # Nutze das Dokument-UUID-Prefix für alle Dateien
        obj_name = f"markdown_docs/{doc.id}/{upload.name}"

        # Lege das Asset mit file an
        asset = EmbeddedAsset.objects.create(
            object_name=obj_name
        )
        asset.file.save(obj_name, upload, save=True)

        doc.embedded_assets.add(asset)

        return JsonResponse({'url': asset.file.url})

class MarkdownDocumentDeleteView(DeleteView):
    model = MARKDOWN_Document
    template_name = 'markdown_document_confirm_delete.html'
    success_url = reverse_lazy('markdown_document_list')

