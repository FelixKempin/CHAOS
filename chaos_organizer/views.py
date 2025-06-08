

import calendar
from datetime import date, datetime, time, timedelta

import numpy as np
from dateutil.rrule import rrulestr
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, DetailView, DeleteView, UpdateView
from chaos_organizer.models import Appointment, ToDo
from chaos_organizer.forms  import AppointmentForm, ToDoForm
from chaos_information.models import Information  # dein Info‐Modell


# ─── Helpers ────────────────────────────────────────────────────────────
def get_events_in_range(start: datetime, end: datetime):
    events = []

    # ─── Termine (Appointment) ───────────────────────────────────────────
    for appt in Appointment.objects.all():
        # 1) Feste (einmalige) Termine:
        if appt.begin < end and appt.end > start:
            events.append({
                'dt': appt.begin,
                'item': appt,
                'type': 'appt',
                'recurring': False
            })

        # 2) Wiederholende Termine per RRULE nur im gewünschten Zeitraum:
        try:
            rrule_obj = appt.get_occurrences()  # liefert ein rrule‐Objekt
            for occ in rrule_obj.between(start, end, inc=True):
                events.append({
                    'dt': occ,
                    'item': appt,
                    'type': 'appt',
                    'recurring': True
                })
        except Exception:
            # Falls irgendetwas schiefgeht (z. B. kein gültiger RRULE), überspringen
            pass

    # ─── To-Dos (Deadline + Wiederholungen) ────────────────────────────────
    for todo in ToDo.objects.all():
        # 1) Fester Deadline-Termin (kein „occurrences“ nötig):
        if todo.deadline and start <= todo.deadline < end:
            events.append({
                'dt': todo.deadline,
                'item': todo,
                'type': 'todo',
                'recurring': False
            })

        # 2) Wiederholende Deadlines per RRULE nur im gewünschten Zeitraum:
        if todo.deadline:
            try:
                rrule_obj = todo.get_occurrences()  # liefert ein rrule‐Objekt
                for occ in rrule_obj.between(start, end, inc=True):
                    events.append({
                        'dt': occ,
                        'item': todo,
                        'type': 'todo',
                        'recurring': True
                    })
            except Exception:
                pass

    # Nach Datum/Uhrzeit sortieren und zurückgeben
    return sorted(events, key=lambda x: x['dt'])

def calendar_view(request):
    """
    Tages-, Wochen- oder Monatsansicht. Filter per ?type=all/appt/todo
    """
    tz          = timezone.get_current_timezone()
    view        = request.GET.get('view', 'month')
    filter_type = request.GET.get('type', 'all')
    today       = timezone.localdate()

    def apply_filter(ev_list):
        if filter_type in ('appt','todo'):
            return [e for e in ev_list if e['type']==filter_type]
        return ev_list

    # je nach view-Parameter start/end berechnen...
    if view == 'day':
        y,m,d = (int(request.GET.get(k,getattr(today,k))) for k in ('year','month','day'))
        current = date(y,m,d)
        start = timezone.make_aware(datetime.combine(current, time.min), tz)
        end   = timezone.make_aware(datetime.combine(current, time.max), tz)
        tpl   = 'calendar/day.html'
        ctx   = {'date': current}

    elif view == 'week':
        year = int(request.GET.get('year', today.year))
        week = int(request.GET.get('week', today.isocalendar()[1]))
        first = date.fromisocalendar(year, week, 1)
        start = timezone.make_aware(datetime.combine(first, time.min), tz)
        end   = start + timedelta(days=7)
        tpl   = 'calendar/week.html'
        ctx   = {'date': first}

    else:  # month
        year  = int(request.GET.get('year', today.year))
        month = int(request.GET.get('month', today.month))
        first = date(year, month, 1)
        cal   = calendar.Calendar()
        month_days = cal.monthdatescalendar(year, month)
        start = timezone.make_aware(datetime.combine(month_days[0][0], time.min), tz)
        end   = timezone.make_aware(datetime.combine(month_days[-1][-1], time.max), tz) + timedelta(days=1)
        raw   = get_events_in_range(start, end)
        evs   = apply_filter(raw)

        # baue Wochen‐Matrix
        day_map = {d:[] for week in month_days for d in week}
        for e in evs:
            day_map[e['dt'].date()].append(e)
        weeks = [
            [{'day': d, 'events': day_map.get(d, [])} for d in week]
            for week in month_days
        ]
        tpl   = 'calendar/month.html'
        ctx   = {'date': first, 'weeks': weeks}

    # Lade & filtere Events und hänge jeweils alle Info‐Objekte an
    if view in ('day','week'):
        evs = apply_filter(get_events_in_range(start, end))
        for e in evs:
            e['infos'] = list(e['item'].information.all())
        ctx['events'] = evs

    # Basis‐Context für Navigation & Filter
    ctx.update({
        'view': view,
        'filter_type': filter_type,
        'view_modes': [('day','Tag'),('week','Woche'),('month','Monat')],
    })
    return render(request, tpl, ctx)


# ─── Appointment Views ──────────────────────────────────────────────────
class AppointmentCreateView(CreateView):
    model         = Appointment
    form_class    = AppointmentForm
    template_name = 'calendar/appointment_form.html'
    success_url   = reverse_lazy('calendar:calendar')


class AppointmentDetailView(DetailView):
    model               = Appointment
    template_name       = 'calendar/appointment_detail.html'
    context_object_name = 'appt'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['information_list'] = list(self.object.information.all())
        return ctx


class AppointmentUpdateView(UpdateView):
    model         = Appointment
    form_class    = AppointmentForm
    template_name = 'calendar/appointment_form.html'
    success_url   = reverse_lazy('calendar:calendar')


class AppointmentDeleteView(DeleteView):
    model         = Appointment
    template_name = 'calendar/appointment_confirm_delete.html'
    success_url   = reverse_lazy('calendar:calendar')


# ─── ToDo Views ────────────────────────────────────────────────────────
class ToDoCreateView(CreateView):
    model         = ToDo
    form_class    = ToDoForm
    template_name = 'calendar/todo_form.html'
    success_url   = reverse_lazy('calendar:calendar')


class ToDoDetailView(DetailView):
    model               = ToDo
    template_name       = 'calendar/todo_detail.html'
    context_object_name = 'todo'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['information_list'] = list(self.object.information.all())
        return ctx


class ToDoUpdateView(UpdateView):
    model         = ToDo
    form_class    = ToDoForm
    template_name = 'calendar/todo_form.html'
    success_url   = reverse_lazy('calendar:calendar')


class ToDoDeleteView(DeleteView):
    model         = ToDo
    template_name = 'calendar/todo_confirm_delete.html'
    success_url   = reverse_lazy('calendar:calendar')


# ─── Recurrences (Recallings) View ─────────────────────────────────────
def recallings_view(request):
    """
    Zeigt die nächsten Wiederkehrenden Ereignisse (Appointment + ToDo) im nächsten Monat an.
    """
    tz          = timezone.get_current_timezone()
    now         = timezone.localtime()
    future      = now + timedelta(days=30)
    recurrences = []

    for appt in Appointment.objects.all():
        for occ in appt.get_occurrences():
            if now <= occ < future:
                recurrences.append({'dt': occ, 'item': appt, 'type': 'appt'})

    for todo in ToDo.objects.all():
        for occ in todo.get_occurrences():
            if now <= occ < future:
                recurrences.append({'dt': occ, 'item': todo, 'type': 'todo'})

    recurrences.sort(key=lambda x: x['dt'])
    return render(request, 'calendar/recurrences.html', {'recurrences': recurrences})