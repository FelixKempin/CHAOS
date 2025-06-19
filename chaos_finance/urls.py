from django.urls import path
from . import views


urlpatterns = [
    path('', views.GoalListView.as_view(), name='goal_list'),
    path('goal/<uuid:pk>/', views.GoalDetailView.as_view(), name='goal_detail'),
    path('goal/create/', views.GoalCreateView.as_view(), name='goal_create'),
    path('goal/<uuid:pk>/update/', views.GoalUpdateView.as_view(), name='goal_update'),
    path('goal/<uuid:pk>/delete/', views.GoalDeleteView.as_view(), name='goal_delete'),
    # mentor/urls.py
    path("advice/<uuid:pk>/delete/", views.delete_advice, name="delete_advice"),
    path("status/<uuid:pk>/delete/", views.delete_status_update, name="delete_status_update"),

]
