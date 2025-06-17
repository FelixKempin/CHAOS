from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView


class JournalListView(ListView):
    model = DailyJournal
    template_name = 'journal_list.html'
    context_object_name = 'daily_journals'
    paginate_by = 20

class JournalDetailView(DetailView):
    model = DailyJournal
    template_name = 'journal_detail.html'
    context_object_name = 'daily_journal'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        return ctx

class JournalCreateView(CreateView):
    model = DailyJournal
    form_class = DailyJournalForm
    template_name = 'journal_form.html'
    success_url = reverse_lazy('journal_list')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        # neu: kein Objekt, also kein Upload-URL
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

class JournalUpdateView(UpdateView):
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

class JournalDeleteView(DeleteView):
    model = MARKDOWN_Document
    template_name = 'markdown_document_confirm_delete.html'
    success_url = reverse_lazy('markdown_document_list')