# templatetags/markdown_tags.py
import markdown
from django import template
from django.utils.safestring import mark_safe

register = template.Library()

@register.filter
def render_markdown(file_field):
    try:
        content = file_field.read().decode("utf-8")
        return mark_safe(markdown.markdown(content))
    except Exception as e:
        return f"<em>Markdown-Fehler: {e}</em>"
