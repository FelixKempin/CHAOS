# main_app/views.py
import openai
from django.conf import settings
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import ListView, CreateView
from .models import Thread, ChatMessage, ThreadContextEntry
from .forms import ThreadForm, ChatMessageForm
from chaos_embeddings.models import Embedding

from chaos_information.models import Information
from chaos_embeddings.services.embedding_service import generate_embedding

from chaos_embeddings.utils import get_similar_embeddings

openai.api_key = settings.OPENAI_API_KEY

client = openai.Client(api_key=settings.OPENAI_API_KEY)


# Kontext holen
def fetch_contextual_information(thread, newest_message_text, top_k=5):
    new_vec = generate_embedding(newest_message_text)
    sims = get_similar_embeddings(vector=new_vec, top_k=top_k)

    context_items = []
    for emb in sims:
        score = emb.distance
        info = emb.content_object
        if not isinstance(info, Information):
            continue  # Sicherheits-Check: Nur echte Information-Objekte verarbeiten

        # Attribut abhängig von Score
        if score > 0.85:
            selected_attr = 'information_long'
        elif score > 0.6:
            selected_attr = 'information_short'
        else:
            selected_attr = 'information_original'

        # Sicherstellen, dass es im Fallback was gibt
        content = getattr(info, selected_attr, '').strip()
        if not content:
            fallback_order = {
                'information_short': ['information_long', 'information_original'],
                'information_long': ['information_original'],
                'information_original': []
            }
            for fallback in fallback_order[selected_attr]:
                content = getattr(info, fallback, '').strip()
                if content:
                    selected_attr = fallback
                    break

        # Save ThreadContextEntry (falls noch nicht da)
        obj, created = ThreadContextEntry.objects.get_or_create(
            thread=thread,
            information=info,
            defaults={'selected_attribute': selected_attr}
        )

        context_items.append({
            'title': info.title,
            'content': content,
            'source': info.information_original,
        })

    return context_items

class ThreadListView(ListView):
    model = Thread
    template_name = 'thread_list.html'
    context_object_name = 'threads'
    paginate_by = 20

class ThreadCreateView(CreateView):
    model = Thread
    form_class = ThreadForm
    template_name = 'thread_form.html'
    success_url = reverse_lazy('thread_list')

class ThreadDetailView(View):
    template_name = 'thread_detail.html'

    def get(self, request, pk):
        thread = get_object_or_404(Thread, pk=pk)
        form = ChatMessageForm()
        messages = thread.messages.all()

        # Kontextobjekte aus Session holen (nach POST)
        context_entries = thread.context_entries.select_related('information')
        context_items = [
            {
                'title': entry.information.title,
                'content': entry.get_content(),
                'source': entry.information.information_original,
            }
            for entry in context_entries
        ]

        return render(request, self.template_name, {
            'thread': thread,
            'messages': messages,
            'form': form,
            'context_items': context_items,
        })

    def post(self, request, pk):
        thread = get_object_or_404(Thread, pk=pk)
        form = ChatMessageForm(request.POST)

        if form.is_valid():
            # 1. User-Nachricht speichern
            msg_user = form.save(commit=False)
            msg_user.thread = thread
            msg_user.sender = 'user'
            msg_user.save()

            # 2. Kontextinformationen via Embeddings holen
            context_items = fetch_contextual_information(thread, msg_user.content)

            # 3. Nachrichtenverlauf für API aufbereiten
            messages_for_api = [
                {'role': 'user' if m.sender == 'user' else 'assistant', 'content': m.content}
                for m in thread.messages.all()
            ]

            # 4. System-Prompt mit Kontext voranstellen
            system_prompt = "\n\n".join(
                f"{ci['title']}: {ci['content']}" for ci in context_items
            )
            messages_for_api.insert(0, {
                'role': 'system',
                'content': f"Nutze nur diese Informationen:\n{system_prompt}"
            })

            # 5. OpenAI-API aufrufen
            from openai import OpenAI
            from django.conf import settings
            client = OpenAI(api_key=settings.OPENAI_API_KEY)

            try:
                response = client.chat.completions.create(
                    model="gpt-4",  # oder gpt-3.5-turbo
                    messages=messages_for_api,
                )
                assistant_text = response.choices[0].message.content
            except Exception as e:
                assistant_text = f"Fehler beim Abruf der Antwort: {str(e)}"

            # 6. Antwort speichern
            ChatMessage.objects.create(
                thread=thread,
                sender='assistant',
                content=assistant_text
            )

            # 7. Kontextobjekte in Session speichern für get()
            request.session['context_items'] = context_items

            return redirect('thread_detail', pk=thread.pk)

        # Wenn Formular ungültig ist
        messages = thread.messages.all()
        return render(request, self.template_name, {
            'thread': thread,
            'messages': messages,
            'form': form,
            'context_items': None,
        })

