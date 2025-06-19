# documents/urls.py
from django.urls import path

from chaos_journal.views import JournalUpdateView, JournalDeleteView, JournalDetailView, JournalCreateView, \
    JournalListView

urlpatterns = [
    path('', JournalListView.as_view(), name='journal_list'),
    path('journal/add', JournalCreateView.as_view(), name='journal_create'),
    path('journal/<uuid:pk>/detail', JournalDetailView.as_view(), name='journal_detail'),
    path('<uuid:pk>/edit/', JournalUpdateView.as_view(), name='journal_update'),
    path('journal/<uuid:pk>/delete', JournalDeleteView.as_view(), name='journal_delete'),


]