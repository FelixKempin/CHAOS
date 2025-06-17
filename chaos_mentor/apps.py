from django.apps import AppConfig


class ChaosMentorConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'chaos_mentor'

    def ready(self):
        # hier werden beim App-Start die Signale registriert
        import chaos_mentor.signals  # noqa

