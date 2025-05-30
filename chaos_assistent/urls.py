# main_app/urls.py
from django.urls import path
from .views import ThreadListView, ThreadCreateView, ThreadDetailView

urlpatterns = [
    path('threads/',            ThreadListView.as_view(),   name='thread_list'),
    path('threads/new/',        ThreadCreateView.as_view(), name='thread_create'),
    path('threads/<uuid:pk>/',  ThreadDetailView.as_view(), name='thread_detail'),
]
