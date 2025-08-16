from django.urls import path
from django.http import JsonResponse
from . import views

def api_index(request):
    """Return a JSON list of available API endpoints."""
    endpoints = {
        "applications": {
            "catalog": "/api/catalog/",
            "logs": "/api/logs/",
            "install": "/api/install/",
        },
        "files": {
            "list": "/api/files/",
            "download": "/api/files/<id>/download/",
        },
        "logs_export": "/api/logs/export/",
        "agent": "/api/agent/",
    }
    return JsonResponse({"endpoints": endpoints})


urlpatterns = [
    # ---------------- API Index ---------------- #
    path("", api_index, name="api_index"),

    # ---------------- Applications ---------------- #
    path("catalog/", views.catalog, name="catalog"),
    path("logs/", views.logs, name="logs"),
    path("install/", views.install_direct, name="install_direct"),

    # ---------------- Files ---------------- #
    path("files/", views.list_files, name="list_files"),
    path("files/<int:file_id>/download/", views.download_file, name="download_file"),

    # ---------------- Logs Export ---------------- #
    path("logs/export/", views.export_logs_excel, name="export_logs_excel"),

    # ---------------- Agent (Groq) ---------------- #
    path("agent/", views.agent_entry, name="agent_entry"),
]