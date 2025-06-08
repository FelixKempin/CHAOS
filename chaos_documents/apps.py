from django.apps import AppConfig

class ChaosDocumentsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'chaos_documents'

    def ready(self):
        # Hier werden beim App-Start die Signale registriert
        import chaos_documents.signals  # noqa
