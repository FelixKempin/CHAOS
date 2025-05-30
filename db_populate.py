# my_ai_app/services/tag_utils.py
from chaos_embeddings.services.embedding_service import generate_embedding
from chaos_information.models import Tag


def populate_initial_tags():
    """
    Legt eine fixe Liste von Standard-Tags an (oder aktualisiert sie) und
    erzeugt für jeden das Embedding, falls noch nicht vorhanden.
    """
    defaults = [
        # Hauptkategorien
        ("Privat", ""),
        ("Geschäftlich", ""),
        ("Finanzen", ""),

        # Privat-Lebensbereiche
        ("Haushalt", ""),
        ("Wohnen", ""),
        ("Miete", ""),
        ("Versicherungen", ""),
        ("Auto", ""),
        ("Gesundheit", ""),
        ("Arztbesuch", ""),
        ("Medikamente", ""),
        ("Fitness", ""),
        ("Training", ""),
        ("Ernährung", ""),
        ("Rezepte", ""),
        ("Mental", ""),
        ("Stressmanagement", ""),
        ("Meditation", ""),
        ("Schlaf", ""),
        ("Freizeit", ""),
        ("Kino", ""),
        ("Event", ""),
        ("Hobby", ""),
        ("Fotografie", ""),
        ("Garten", ""),
        ("Musik", ""),
        ("Reise", ""),
        ("Inland", ""),
        ("International", ""),
        ("Planung", ""),
        ("Familie", ""),
        ("Eltern", ""),
        ("Kinder", ""),
        ("Beziehungen", ""),
        ("Freunde", ""),
        ("Geburtstag", ""),
        ("Urlaub", ""),

        # Geschäftlich-Prozesse & -Projekte
        ("Projekt", ""),
        ("Projekt Planung", ""),
        ("Projekt Status", ""),
        ("Meeting", ""),
        ("Meeting Team", ""),
        ("Meeting Kunde", ""),
        ("Protokoll", ""),
        ("Kunde", ""),
        ("Lieferant", ""),
        ("Vertrieb", ""),
        ("Leads", ""),
        ("Marketing", ""),
        ("Kampagne", ""),
        ("SEO", ""),
        ("Public Relations", ""),
        ("Customer Success", ""),
        ("Onboarding", ""),
        ("Support", ""),
        ("IT", ""),
        ("Infrastruktur", ""),
        ("Softwareentwicklung", ""),
        ("Entwicklung", ""),
        ("Design", ""),
        ("Test", ""),
        ("Deployment", ""),
        ("Backup", ""),
        ("Compliance", ""),
        ("Rechtsangelegenheiten", ""),

        # Finanz-Themen
        ("Budget", ""),
        ("Rechnung", ""),
        ("Beleg", ""),
        ("Zahlung", ""),
        ("Mahnung", ""),
        ("Bank", ""),
        ("Kreditkarte", ""),
        ("Darlehen", ""),
        ("Hypothek", ""),
        ("Investitionen", ""),
        ("Aktien", ""),
        ("ETFs", ""),
        ("Immobilien Invest", ""),
        ("Sparen", ""),
        ("Steuer", ""),
        ("Jahresabschluss", ""),
        ("Prognose", ""),
        ("Audit", ""),

        # Administration & Aufgaben
        ("Termin", ""),
        ("To-Do", ""),
        ("Auftrag", ""),
        ("Angebot", ""),
        ("Vertrag", ""),
        ("Aufgabe Dringend", ""),
        ("Aufgabe Wichtig", ""),
        ("Strategie", ""),
        ("Analyse", ""),
        ("Bericht", ""),
        ("Dokumentation", ""),
        ("Qualität", ""),
        ("Audit Compliance", ""),

        # Kommunikation & Medien
        ("E-Mail", ""),
        ("Telefon", ""),
        ("Notiz", ""),
        ("Schnellnotiz", ""),
        ("Entwurf", ""),
        ("Feedback", ""),
        ("Internes Feedback", ""),
        ("Externes Feedback", ""),
        ("Blog", ""),
        ("Podcast", ""),
        ("Webinar", ""),
        ("Konferenz", ""),
        ("Workshop", ""),

        # Lernen & Weiterbildung
        ("Studium", ""),
        ("Vorlesung", ""),
        ("Seminar", ""),
        ("Klausur", ""),
        ("Praktikumstermin", ""),
        ("Abschlussarbeit", ""),
        ("Schule", ""),
        ("Klassenarbeit", ""),
        ("Hausaufgabe", ""),
        ("Weiterbildung", ""),
        ("Kurs", ""),
        ("Zertifikat", ""),
        ("Mitschrift", ""),
        ("Zusammenfassung", ""),
        ("Übungsaufgabe", ""),
        ("Karteikarte", ""),
        ("Forschung", ""),

        # Karriere & Networking
        ("Karriere", ""),
        ("Bewerbung", ""),
        ("Karriere Ziele", ""),
        ("Interview", ""),
        ("Networking", ""),
        ("Mentoring", ""),

        # Technik & Digitales
        ("Programmierung", ""),
        ("Tool", ""),
        ("Lizenz", ""),
        ("Data Science", ""),
        ("Künstliche Intelligenz", ""),
        ("Maschinelles Lernen", ""),
        ("Import", ""),
        ("Export", ""),
        ("Statistik", ""),

        # Mobilität & Logistik
        ("Transport", ""),
        ("Route", ""),
        ("Logistik", ""),
        ("Versand", ""),

        # Immobilien & Energie
        ("Immobilien", ""),
        ("Haus", ""),
        ("Haus Wartung", ""),
        ("Gartenpflege", ""),
        ("Strom", ""),
        ("Gas", ""),

        # Umwelt & Nachhaltigkeit
        ("Umwelt", ""),
        ("Nachhaltigkeit", ""),
        ("CSR", ""),
        ("CO2-Bilanz", ""),

        # Kultur & Unterhaltung
        ("Kultur", ""),
        ("Kunst", ""),
        ("Musik", ""),
        ("Film", ""),
        ("Literatur", ""),
        ("Gaming", ""),

        # Sonstiges
        ("Idee", ""),
        ("Business Idee", ""),
        ("Persönliche Idee", ""),
        ("Innovation", ""),
        ("Kurzfristige Ziele", ""),
        ("Langfristige Ziele", ""),
        ("Journal", ""),
        ("Fehler", ""),
        ("Wartung", ""),
        ("Problem", ""),

    ]

    for name, desc in defaults:
        tag, created = Tag.objects.get_or_create(
            name=name,
            defaults={"description": desc}
        )
        if created:
            print(f"Angelegt: {name}")
        else:
            print(f"Existiert bereits: {name}")


    print("Fertig: Standard-Tags angelegt/aktualisiert.")
