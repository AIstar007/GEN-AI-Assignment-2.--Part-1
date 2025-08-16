# core/views.py
import os, io, json, traceback, datetime as dt
import pandas as pd
from django.http import JsonResponse, FileResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from rest_framework.decorators import api_view
from rest_framework.response import Response
from groq import Groq

from .models import ApplicationCatalog, InstallLog, File
from .sn_excel import append_request

# --------------------------- INIT GROQ --------------------------- #
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

def groq_chat(messages, model="llama-3.1-8b-instant"):
    try:
        resp = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.3,
        )
        return resp.choices[0].message.content
    except Exception as e:
        return f"(Groq error: {e})"

# --------------------------- APPLICATIONS --------------------------- #
@api_view(["GET"])
def catalog(request):
    """Return list of available applications"""
    apps = ApplicationCatalog.objects.order_by("app_name")
    data = [
        {
            "app_name": app.app_name,
            "versions": app.version_list(),
            "description": app.description,
        }
        for app in apps
    ]
    return Response(data)

@api_view(["GET"])
def logs(request):
    """Return install logs (optionally filtered by app)"""
    app = request.query_params.get("app")
    qs = InstallLog.objects.select_related("app").order_by("-timestamp")[:200]
    if app:
        qs = qs.filter(app__app_name=app)

    data = [
        {
            "timestamp": l.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "app": l.app.app_name if l.app else None,
            "version": l.version,
            "status": l.status,
            "user_prompt": l.user_prompt,
        }
        for l in qs
    ]
    return Response(data)

@api_view(["POST"])
def install_direct(request):
    """Direct install trigger (UI button can use this)"""
    app_name = request.data.get("app_name")
    version = request.data.get("version")
    note = request.data.get("note", "")

    if not app_name or not version:
        return Response({"detail": "app_name and version required"}, status=400)

    app = ApplicationCatalog.objects.filter(app_name=app_name).first()
    if not app:
        return Response({"detail": "App not found"}, status=404)
    if version not in app.version_list():
        return Response({"detail": "Version not available"}, status=400)

    req_id = append_request(note or f"Install {app_name} {version}", app_name, version, status="Installed")
    InstallLog.objects.create(user_prompt=note, app=app, version=version, status="Installed")

    return Response({
        "message": f"Installed (simulated) {app_name} {version}",
        "request_id": req_id
    })

# --------------------------- FILES --------------------------- #
@api_view(["GET"])
def list_files(request):
    """Role-based file listing"""
    role = request.query_params.get("role", "user")

    if role in ("admin", "manager"):
        files = File.objects.all().order_by("-is_public", "filename")
    else:
        files = File.objects.filter(is_public=True).order_by("filename")

    data = [{"id": f.id, "filename": f.filename, "is_public": f.is_public} for f in files]
    return Response(data)

@api_view(["GET"])
def download_file(request, file_id):
    """Dummy file download, respecting role permissions"""
    role = request.query_params.get("role", "user")
    f = File.objects.filter(id=file_id).first()
    if not f:
        return Response({"detail": "File not found"}, status=404)
    if not f.is_public and role not in ("admin", "manager"):
        return Response({"detail": "Forbidden"}, status=403)

    buf = io.BytesIO()
    buf.write(f"Dummy file: {f.filename}\nGenerated at {dt.datetime.now()}".encode())
    buf.seek(0)
    return FileResponse(buf, as_attachment=True, filename=f.filename)

# --------------------------- EXPORT LOGS --------------------------- #
@api_view(["GET"])
def export_logs_excel(request):
    """Export logs filtered by role/user to Excel"""
    role = request.query_params.get("role", "user")
    user = request.query_params.get("user", "")

    if role in ("admin", "manager"):
        logs = InstallLog.objects.all().order_by("-timestamp")
    else:
        logs = InstallLog.objects.filter(user_prompt__icontains=user).order_by("-timestamp")

    rows = [
        {
            "timestamp": l.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "app": l.app.app_name if l.app else None,
            "version": l.version,
            "status": l.status,
            "user_prompt": l.user_prompt,
        }
        for l in logs
    ]

    df = pd.DataFrame(rows or [])
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as xw:
        (df if not df.empty else pd.DataFrame({"info": ["no logs"]})).to_excel(xw, index=False, sheet_name="logs")
    output.seek(0)
    return FileResponse(output, as_attachment=True, filename="deployment_logs.xlsx")

# --------------------------- AGENT --------------------------- #
@csrf_exempt
@require_http_methods(["POST"])
def agent_entry(request):
    """Groq agent → classify intent: install/download app or file, else fallback chat"""
    try:
        data = json.loads(request.body)
        text = data.get("input", "").strip()
        if not text:
            return JsonResponse({"detail": "Input required"}, status=400)

        # Ask Groq to classify
        classification = groq_chat([
            {"role": "system", "content": "Classify if text is about installing/downloading software or files."},
            {"role": "user", "content": f"Text: {text}. Reply JSON with keys: intent, app, version, file"}
        ])

        try:
            parsed = json.loads(classification)
        except Exception:
            parsed = {"intent": "other"}

        # ---------------- APP / FILE INTENTS ---------------- #
        if parsed.get("intent") in ["install", "download"]:
            if parsed.get("file"):   # File download
                fname = parsed["file"]
                f = File.objects.filter(filename__icontains=fname).first()
                if not f:
                    return JsonResponse({"detail": f"File '{fname}' not found"}, status=404)
                return JsonResponse({
                    "message": f"📂 File '{f.filename}' ready to download",
                    "file_id": f.id
                })

            # Application case
            app_name = parsed.get("app")
            version = parsed.get("version")

            if not app_name:
                return JsonResponse({"detail": "Which application do you want to install/download?"}, status=200)

            app = ApplicationCatalog.objects.filter(app_name__iexact=app_name).first()
            if not app:
                return JsonResponse({"detail": f"App '{app_name}' not found"}, status=404)

            available_versions = app.version_list()
            if version and version not in available_versions:
                return JsonResponse({
                    "detail": f"Version not available. Choose from {available_versions}"
                }, status=400)

            chosen_version = version or available_versions[-1]
            InstallLog.objects.create(user_prompt=text, app=app, version=chosen_version, status="Installed")

            return JsonResponse({
                "message": f"✅ {parsed['intent'].title()}ed {app_name} {chosen_version} (simulated)",
                "app": app_name,
                "version": chosen_version,
                "status": "Installed"
            })

        # ---------------- FALLBACK ---------------- #
        reply = groq_chat([
            {"role": "system", "content": "You are a helpful IT support assistant."},
            {"role": "user", "content": text}
        ])
        return JsonResponse({"output": reply})

    except Exception as e:
        traceback.print_exc()
        return JsonResponse({"detail": f"Agent error: {e}"}, status=500)