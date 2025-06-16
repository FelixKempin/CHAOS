import re

def md_to_text(raw: str) -> str:
    """
    Wandelt einfachen Markdown-Text in „rohen“ Klartext um,
    indem Bilder-/Link-Syntax sowie Überschriften- und Listenmarker entfernt werden.
    """
    text = raw

    # 1) Bilder rausschmeißen: ![Alt](url)
    text = re.sub(r'!\[.*?\]\(.*?\)', '', text)

    # 2) Links umwandeln: [Label](url) → Label
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)

    # 3) Überschriften entfernen: leading #...
    text = re.sub(r'(^|\n)[ \t]*#{1,6}[ \t]*', r'\1', text)

    # 4) Listenmarker entfernen: -, *, + am Zeilenanfang
    text = re.sub(r'(^|\n)[ \t]*[\-\*\+][ \t]+', r'\1', text)

    # 5) Blockquotes entfernen: > am Zeilenanfang
    text = re.sub(r'(^|\n)[ \t]*>[ \t]?', r'\1', text)

    # 6) Over-strip: mehrere Leerzeilen → eine Leerzeile
    text = re.sub(r'\n{3,}', '\n\n', text)

    return text.strip()
