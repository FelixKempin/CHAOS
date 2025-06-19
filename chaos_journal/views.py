from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView

from .forms import DailyJournalForm
from .models import DailyJournal


class JournalListView(ListView):
    model = DailyJournal
    template_name = 'journal_list.html'
    context_object_name = 'daily_journals'
    paginate_by = 20


class JournalDetailView(DetailView):
    model = DailyJournal
    template_name = 'journal_detail.html'
    context_object_name = 'daily_journal'


class JournalCreateView(CreateView):
    model = DailyJournal
    form_class = DailyJournalForm
    template_name = 'journal_form.html'
    success_url = reverse_lazy('journal_list')


class JournalUpdateView(UpdateView):
    model = DailyJournal
    form_class = DailyJournalForm
    template_name = 'journal_form.html'
    success_url = reverse_lazy('journal_list')


class JournalDeleteView(DeleteView):
    model = DailyJournal
    template_name = 'journal_confirm_delete.html'
    success_url = reverse_lazy('journal_list')
