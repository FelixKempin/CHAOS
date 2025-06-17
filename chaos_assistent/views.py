# main_app/views.py
import openai
from django.conf import settings
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import ListView, CreateView
from .models import Thread, ChatMessage
from .forms import ThreadForm, ChatMessageForm
from chaos_embeddings.models import Embedding


from chaos_embeddings.services.embedding_service import generate_embedding
openai.api_key = settings.OPENAI_API_KEY

client = openai.Client(api_key=settings.OPENAI_API_KEY)

# Hilfsfunktion: Kontextelemente holen über Embeddings
def fetch_contextual_information(thread, newest_message_text, top_k=5):
    """
    1. Embedding des neuen Texts erzeugen (z.B. via Deinen Embedding-Service).
    2. In chaos_embeddings Embedding.objects.similar(...) nach passenden Information-Objekten suchen.
    3. Nach Relevanz filtern und nur information_short / information_long laden je nach Score.
    4. Rückgabe: Liste von dicts {'info': Information, 'attribute': 'information_short'}
    """
    # Pseudocode – bitte mit Deinem actual Embedding-Client ersetzen:
    new_vec = generate_embedding(newest_message_text)
    sims = Embedding.objects.get_similar(vector=new_vec, top_k=top_k)
    context = []
    for emb, score in sims:
        info = emb.content_object  # Information-Instanz
        # Beispiel-Schwellen:
        if score > 0.8:
            attr = 'information_long'
        else:
            attr = 'information_short'
        context.append({
            'title': info.title,
            'content': getattr(info, attr),
            'source': info.information_original,
        })
    return context

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
        return render(request, self.template_name, {
            'thread': thread,
            'messages': messages,
            'form': form,
        })

    def post(self, request, pk):
        thread = get_object_or_404(Thread, pk=pk)
        form = ChatMessageForm(request.POST)
        if form.is_valid():
            # 1) User-Nachricht speichern
            msg_user = form.save(commit=False)
            msg_user.thread = thread
            msg_user.sender = 'user'
            msg_user.save()
            # 2) Kontext über Embeddings holen
            context_items = fetch_contextual_information(thread, msg_user.content)
            # 3) Anfrage an Chat‐Assistenten bauen
            messages_for_api = []
            for m in thread.messages.all():
                role = 'user' if m.sender == 'user' else 'assistant'
                messages_for_api.append({'role': role, 'content': m.content})
            # Kontext vorne einschleusen
            system_prompt = "\n\n".join(
                f"{ci['title']}: {ci['content']}" for ci in context_items
            )
            messages_for_api.insert(0, {
                'role': 'system',
                'content': f"Nutze nur diese Informationen:\n{system_prompt}"
            })

            response = client.chat(messages_for_api)
            assistant_text = response.choices[0].message.content
            # 5) Antwort speichern
            ChatMessage.objects.create(
                thread=thread,
                sender='assistant',
                content=assistant_text
            )
            return redirect('thread_detail', pk=thread.pk)
        # bei Fehlern
        messages = thread.messages.all()
        return render(request, self.template_name, {
            'thread': thread, 'messages': messages, 'form': form
        })
