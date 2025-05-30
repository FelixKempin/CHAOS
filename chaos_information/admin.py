from django.contrib import admin
from .models import (
    Agent,
    Action,
    UserAction,
    Tag,
    Vault,
    Folder,
    Information,
    ReviewProposal,
    RelevanceEvent,
    TextInput,
    RequiredInformation,

)

# Alle Models im Admin registrieren
models_to_register = [
    Agent,
    Action,
    UserAction,
    Tag,
    Vault,
    Folder,
    Information,
    ReviewProposal,
    RelevanceEvent,
    TextInput,
    RequiredInformation,

]

for model in models_to_register:
    admin.site.register(model)