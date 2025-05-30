from django.apps import AppConfig

class ChaosInformationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'chaos_information'

    def ready(self):
        # hier werden beim App-Start die Signale registriert
        import chaos_information.signals  # noqa
