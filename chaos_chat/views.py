import os

from chaos_chat.forms import ChatForm
from chaos_documents.models import TEXT_Document, CSV_Document, MARKDOWN_Document, IMG_Document, PDF_Document
from chaos_information.models import TextInput
from django.contrib.contenttypes.models import ContentType
from django.shortcuts import redirect, render

from chaos_information.models import Information

from chaos_information.models import Vault


def chat_view(request):
    history = request.session.setdefault("chat_history", [])

    # Vorauswahl für Vault aus der Session holen
    initial = {}
    selected_vault_id = request.session.get("selected_vault_id")
    if selected_vault_id:
        try:
            initial["vault"] = Vault.objects.get(id=selected_vault_id)
        except Vault.DoesNotExist:
            pass

    if request.method == "POST":
        form = ChatForm(request.POST, request.FILES)
        if form.is_valid():
            text  = form.cleaned_data["text"]
            file  = form.cleaned_data["file"]
            image = form.cleaned_data["image"]
            vault = form.cleaned_data["vault"]

            # Vault in der Session merken
            if vault:
                request.session["selected_vault_id"] = str(vault.id)

            # 1) User-Nachricht in History
            if text and not file and not image:
                history.append({"sender": "user", "text": text})
            elif file:
                history.append({"sender": "user", "text": f"Datei: {file.name}"})
            else:
                history.append({"sender": "user", "text": "Bild-Upload"})

            # 2) Dokument anlegen
            info_obj = None

            if file:
                name, ext = os.path.splitext(file.name.lower())
                doc_model = None

                if ext == ".pdf":
                    doc_model = PDF_Document
                elif ext == ".txt":
                    doc_model = TEXT_Document
                elif ext == ".csv":
                    doc_model = CSV_Document
                elif ext == ".md":
                    doc_model = MARKDOWN_Document
                else:
                    history.append({
                        "sender": "bot",
                        "text": f"❌ Unbekannter Dateityp: {ext}"
                    })
                    request.session.modified = True
                    return redirect("chat")

                doc = doc_model.objects.create(file=file, meta_description=text or "")
                info_obj = doc

            elif image:
                doc = IMG_Document.objects.create(file=image, meta_description=text or "")
                info_obj = doc

            elif text:
                doc = TextInput.objects.create(text=text)
                info_obj = doc

            # 2b) Information verknüpfen, wenn möglich
            if info_obj:
                content_type = ContentType.objects.get_for_model(info_obj.__class__)
                Information.objects.create(
                    title=str(info_obj),
                    content_type=content_type,
                    object_id=str(info_obj.id),
                    object_type_string=content_type.model,
                    vault=vault  # optional
                )

            # 3) Bot-Bestätigung
            history.append({
                "sender": "bot",
                "text": "👍 Deine Eingabe wurde angenommen und läuft nun asynchron durch unsere Tasks."
            })

            request.session.modified = True
            return redirect("chat")

    else:
        form = ChatForm(initial=initial)

    return render(request, "chat.html", {
        "form": form,
        "history": history
    })


# Create your views here.
