# documents/urls.py
from django.urls import path




urlpatterns = [
    path('journal/', JournalListView.as_view(), name='journal_list'),
    path('journal/add', JournalCreateView.as_view(), name='journal_add'),
    path('journal/<uuid:pk>/edit', JournalUpdateView.as_view(), name='journal_edit'),
    path('journal/<uuid:pk>/delete', JournalDeleteView.as_view(), name='journal_delete'),

]