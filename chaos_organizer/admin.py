from django.contrib import admin
from .models import (

    Appointment,
    ToDo,
)

# Alle Models im Admin registrieren
models_to_register = [

    Appointment,
    ToDo,
]

for model in models_to_register:
    admin.site.register(model)