import os

from chaos_chat.forms import ChatForm
from chaos_documents.models import TEXT_Document, CSV_Document, MARKDOWN_Document, IMG_Document, PDF_Document
from chaos_information.models import TextInput


def chat_view(request):
    history = request.session.setdefault("chat_history", [])

    if request.method == "POST":
        form = ChatForm(request.POST, request.FILES)
        if form.is_valid():
            text  = form.cleaned_data["text"]
            file  = form.cleaned_data["file"]
            image = form.cleaned_data["image"]

            # 1) User-Nachricht in History
            if text and not file and not image:
                history.append({"sender": "user", "text": text})
            elif file:
                history.append({"sender": "user", "text": f"Datei: {file.name}"})
            else:
                history.append({"sender": "user", "text": "Bild-Upload"})

            # 2) Document Anlage – SIGNALS schieben die Tasks nach
            if file:
                name, ext = os.path.splitext(file.name.lower())
                if ext == ".pdf":
                    PDF_Document.objects.create(file=file, meta_description=text or "")
                elif ext == ".txt":
                    TEXT_Document.objects.create(file=file, meta_description=text or "")
                elif ext == ".csv":
                    CSV_Document.objects.create(file=file, meta_description=text or "")
                elif ext == ".md":
                    MARKDOWN_Document.objects.create(file=file, meta_description=text or "")
                else:
                    history.append({
                        "sender": "bot",
                        "text": f"❌ Unbekannter Dateityp: {ext}"
                    })
                    request.session.modified = True
                    return redirect("chat")

            elif image:
                IMG_Document.objects.create(file=image, meta_description=text or "")

            else:
                TextInput.objects.create(text=text)



            # 3) Bot-Bestätigung
            history.append({
                "sender": "bot",
                "text": "👍 Deine Eingabe wurde angenommen und läuft nun asynchron durch unsere Tasks."
            })

            request.session.modified = True
            return redirect("chat")
    else:
        form = ChatForm()

    return render(request, "chat.html", {
        "form": form,
        "history": history
    })
from django.shortcuts import render, redirect

# Create your views here.
