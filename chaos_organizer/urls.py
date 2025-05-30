# organizer_agent_app/urls.py
from django.urls import path
from . import views

app_name = 'calendar'

urlpatterns = [
    # Kalender-Ansicht
    path('', views.calendar_view, name='calendar'),

    # Appointment erzeugen und ansehen
    path('appointment/add/',          views.AppointmentCreateView.as_view(), name='appointment_add'),
    path('appointment/<int:pk>/',     views.AppointmentDetailView.as_view(),   name='appointment_detail'),

    # ToDo erzeugen und ansehen
    path('todo/add/',                 views.ToDoCreateView.as_view(),   name='todo_add'),
    path('todo/<int:pk>/',            views.ToDoDetailView.as_view(), name='todo_detail'),
]
