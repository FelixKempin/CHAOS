from django.apps import AppConfig


class ChaosJournalConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'chaos_journal'

    def ready(self):
        # hier werden beim App-Start die Signale registriert
        import chaos_journal.signals  # noqa
