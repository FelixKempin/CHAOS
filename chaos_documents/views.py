# chaos_documents/views.py
from django.views.generic import ListView, DetailView, CreateView, UpdateView, View
from django.urls import reverse_lazy, reverse
from django.http import JsonResponse
from django.core.files.base import ContentFile
from .models import MARKDOWN_Document
from .forms import MarkdownDocumentForm

class MarkdownDocumentListView(ListView):
    model = MARKDOWN_Document
    template_name = 'markdown_document_list.html'
    context_object_name = 'markdown_docs'
    paginate_by = 20

class MarkdownDocumentDetailView(DetailView):
    model = MARKDOWN_Document
    template_name = 'markdown_document_detail.html'
    context_object_name = 'markdown_doc'

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
        # initialer Datei-Inhalt
        data = ''
        if self.object.file:
            data = self.object.file.open('rb').read().decode('utf-8')
        ctx['initial_markdown'] = data
        # Upload-URL aus reverse()
        ctx['upload_url'] = reverse('md_image_upload', kwargs={'pk': self.object.pk})
        return ctx

    def form_valid(self, form):
        # wie gehabt
        self.object = form.save(commit=False)
        self.object.save()
        content = self.request.POST.get('file_content', '')
        self.object.file.save(
            f'{self.object.pk}.md',
            ContentFile(content.encode('utf-8')),
            save=True
        )
        return super().form_valid(form)


class MarkdownImageUploadView(View):
    """
    Speichert ein einzelnes Bild zum Markdown-Objekt und liefert die URL zurück.
    """
    def post(self, request, pk):
        try:
            doc = MARKDOWN_Document.objects.get(pk=pk)
        except MARKDOWN_Document.DoesNotExist:
            return JsonResponse({'error': 'Nicht gefunden'}, status=404)

        img = request.FILES.get('file')
        if not img:
            return JsonResponse({'error': 'Kein File'}, status=400)

        doc.markdown_image.save(img.name, img, save=True)
        return JsonResponse({'url': doc.markdown_image.url})
