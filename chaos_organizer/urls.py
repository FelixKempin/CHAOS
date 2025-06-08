# organizer_agent_app/urls.py
from django.urls import path
from . import views

app_name = 'calendar'

# organizer_agent_app/urls.py (bzw. euer calendar-urls.py)
from django.urls import path
from . import views

app_name = 'calendar'

urlpatterns = [
    # Kalender-Ansicht
    path('', views.calendar_view, name='calendar'),

    # Appointment: Erzeugen, Detail, Update, Delete
    path('appointment/add/',          views.AppointmentCreateView.as_view(), name='appointment_add'),
    path('appointment/<int:pk>/',     views.AppointmentDetailView.as_view(),   name='appointment_detail'),
    path('appointment/<int:pk>/edit/',   views.AppointmentUpdateView.as_view(),   name='appointment_update'),
    path('appointment/<int:pk>/delete/', views.AppointmentDeleteView.as_view(),   name='appointment_delete'),

    # ToDo: Erzeugen, Detail, Update, Delete
    path('todo/add/',                 views.ToDoCreateView.as_view(),      name='todo_add'),
    path('todo/<int:pk>/',            views.ToDoDetailView.as_view(),      name='todo_detail'),
    path('todo/<int:pk>/edit/',       views.ToDoUpdateView.as_view(),      name='todo_update'),
    path('todo/<int:pk>/delete/',     views.ToDoDeleteView.as_view(),      name='todo_delete'),

    # Recurring Events (Recallings)
    path('recallings/',               views.recallings_view,               name='recallings'),
]
