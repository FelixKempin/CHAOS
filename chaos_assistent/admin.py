from django.contrib import admin
from .models import (

    Thread,
    ChatMessage,

)

# Alle Models im Admin registrieren
models_to_register = [

    Thread,
    ChatMessage,

]

for model in models_to_register:
    admin.site.register(model)