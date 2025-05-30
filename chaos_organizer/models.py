from django.db import models
from django.contrib.contenttypes.fields import GenericRelation
from dateutil.rrule import rrulestr
from django.utils.translation import gettext_lazy as _

from chaos_information.models import Information

# --- Choice-Definitionen ---
PRIORITY_CHOICES = [
    ('low',    _('Low')),
    ('medium', _('Medium')),
    ('high',   _('High')),
]

FREQ_CHOICES = [
    ('DAILY',   _('Täglich')),
    ('WEEKLY',  _('Wöchentlich')),
    ('MONTHLY', _('Monatlich')),
    ('YEARLY',  _('Jährlich')),
]

# --- Abstrakte Basisklasse für wiederholbare Events ---
class RepeatableEvent(models.Model):
    frequency  = models.CharField(
        max_length=10, choices=FREQ_CHOICES, default='WEEKLY',
        help_text=_('Wie oft soll das Event wiederholt werden?')
    )
    interval   = models.PositiveIntegerField(
        default=1,
        help_text=_('Wiederhole alle `interval` Einheiten, z.B. alle 2 Wochen.')
    )
    by_weekday = models.CharField(
        max_length=20, blank=True,
        help_text=_('Nur bei WEEKLY: z.B. "MO,WE,FR".')
    )
    end_date   = models.DateField(
        null=True, blank=True,
        help_text=_('Bis zu welchem Datum soll die Wiederholung laufen?')
    )

    class Meta:
        abstract = True

    def _build_rrule(self, dtstart):
        rule = f"FREQ={self.frequency};INTERVAL={self.interval}"
        if self.frequency == 'WEEKLY' and self.by_weekday:
            rule += f";BYDAY={self.by_weekday}"
        if self.end_date:
            rule += f";UNTIL={self.end_date.strftime('%Y%m%d')}"
        return rrulestr(rule, dtstart=dtstart)

    def get_occurrences(self, dtstart):
        """
        Liefert alle Start-Zeiten gemäß der RecurrenceRule.
        Wird in Subklassen mit dem jeweiligen dtstart-Attribut aufgerufen.
        """
        return self._build_rrule(dtstart)

# --- Appointment-Modell mit Wiederholung ---
class Appointment(RepeatableEvent):
    title       = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    begin       = models.DateTimeField()
    end         = models.DateTimeField()
    priority    = models.CharField(max_length=6, choices=PRIORITY_CHOICES)
    information = GenericRelation(Information)

    def __str__(self):
        return self.title

    def get_occurrences(self):
        # dtstart ist hier self.begin
        return super().get_occurrences(self.begin)

# --- ToDo-Modell mit Wiederholung ---
class ToDo(RepeatableEvent):
    title        = models.CharField(max_length=100)
    description  = models.TextField(blank=True, null=True)
    deadline     = models.DateTimeField(blank=True, null=True)
    priority     = models.CharField(max_length=6, choices=PRIORITY_CHOICES)
    dependencies = models.ManyToManyField(
        'self', blank=True, symmetrical=False, related_name='dependents'
    )
    information = GenericRelation(Information)

    @property
    def is_ready(self):
        return all(getattr(dep, 'completed', False) for dep in self.dependencies.all())

    def get_occurrences(self):
        # Keine Recurrence wenn kein Deadline-Datum gesetzt
        if not self.deadline:
            return []
        return super().get_occurrences(self.deadline)
