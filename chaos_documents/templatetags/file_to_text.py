from django import template

register = template.Library()

@register.filter
def file_to_text(filefield):
    """
    Liest den gesamten Inhalt eines FileField (z.B. .md-Datei)
    und gibt ihn als UTF-8-dekodierten String zurück.
    """
    # Datei öffnen (öffnet im Binary-Modus)
    file_obj = filefield.open('rb')
    try:
        raw = file_obj.read()
        text = raw.decode('utf-8')
    finally:
        # immer schließen, damit kein Handle offen bleibt
        filefield.close()
    return text
