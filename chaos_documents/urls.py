# documents/urls.py
from django.urls import path
from .views import (
    MarkdownDocumentListView,
    MarkdownDocumentDetailView,
    MarkdownDocumentCreateView,
    MarkdownDocumentUpdateView, MarkdownImageUploadView, MarkdownDocumentDeleteView,
)

urlpatterns = [
    path('markdown/', MarkdownDocumentListView.as_view(), name='markdown_document_list'),
    path('markdown/add/', MarkdownDocumentCreateView.as_view(), name='markdown_document_add'),
    path('markdown/<uuid:pk>/', MarkdownDocumentDetailView.as_view(), name='markdown_document_detail'),
    path('markdown/<uuid:pk>/edit/', MarkdownDocumentUpdateView.as_view(), name='markdown_document_edit'),
    path('api/markdown/<uuid:pk>/upload-image/', MarkdownImageUploadView.as_view(), name='md_image_upload'),
    path('markdown/<uuid:pk>/delete/', MarkdownDocumentDeleteView.as_view(), name='markdown_document_delete'),
]