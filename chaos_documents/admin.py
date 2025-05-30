from django.contrib import admin
from .models import (

    IMG_Document,
    PDF_Document,
    CSV_Document,
    TEXT_Document,
    MARKDOWN_Document,
    AUDIO_Document,

)

# Alle Models im Admin registrieren
models_to_register = [
    IMG_Document,
    PDF_Document,
    CSV_Document,
    TEXT_Document,
    MARKDOWN_Document,
    AUDIO_Document,
]

for model in models_to_register:
    admin.site.register(model)