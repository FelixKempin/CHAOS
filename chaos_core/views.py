from django.views.generic import TemplateView

class DashboardView(TemplateView):
    template_name = "dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["sections"] = [
            {
                "title": "Hinzufügen",
                "items": [
                    {"title": "Markdown-Notiz",       "icon": "md_add.png",         "url": "/documents/markdown/add"},
                    {"title": "Text-Notiz", "icon": "txt_add.png", "url": "/chat/chat/"},
                    {"title": "PDF", "icon": "pdf_add.png",         "url": "/chat/chat/"},
                    {"title": "Bild", "icon": "img_add.png", "url": "/chat/chat/"},
                    {"title": "Aufgabe",     "icon": "todo_add.png",        "url": "/organizer/todo/add/"},
                    {"title": "Termin",      "icon": "appointment_add.png", "url": "/organizer/appointment/add/"},
                    {"title": "Journal", "icon": "journal_add.png", "url": "/journal/journal/add"},
                    {"title": "Ziel", "icon": "goal_add.png", "url": "/mentor/goal/create"},
                ],
            },
            {
                "title": "Module",
                "items": [
                    {"title": "Informationen (Liste)", "icon": "information.png",    "url": "/information/information/"},
                    {"title": "Informationen (Map)", "icon": "embedding_map.png", "url": "/information/embedding-map/"},
                    {"title": "Chat", "icon": "chat.png", "url": "/assistent/threads/"},
                    {"title": "Organizer", "icon": "appointment.png", "url": "/organizer/"},
                    {"title": "Ziele",         "icon": "goal.png",           "url": "/mentor"},
                    {"title": "Journal",       "icon": "journal.png",        "url": "/journal"},
                ],
            },
        ]
        return context
