from rest_framework import viewsets
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from .models import Task, Log
from .serializers import TaskSerializer, LogSerializer
import re


# ----------------- VIEWSETS ----------------- #
class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer


class LogViewSet(viewsets.ModelViewSet):
    queryset = Log.objects.all().order_by("-timestamp")
    serializer_class = LogSerializer


# ----------------- SIMPLE VIEWS ----------------- #
def home(request):
    return HttpResponse("Hello 👋, Django API is running! Go to /api/tasks/")


@api_view(["POST"])
def agent_view(request):
    """Agent endpoint: handles install/download commands, logs, and chat fallback."""
    user_input = request.data.get("input", "")
    user = request.data.get("user", "demo")  # default user

    # Detect install or download
    m = re.match(r".*(install|download)\s+(?P<app>[A-Za-z0-9_\-]+)\s*(?P<version>[\d\.]*)", user_input, re.I)
    if m:
        action_type = m.group(1).lower()
        app = m.group("app")
        version = m.group("version") or "latest"
        message = f"✅ {action_type.capitalize()}ed {app} version {version}"

        Log.objects.create(
            user=user,
            log_type="INSTALL" if action_type == "install" else "DOWNLOAD",
            action=message,
        )

        return Response({"message": message, "app": app, "version": version})

    # Otherwise → fallback
    output = f"🤖 You said: {user_input}"
    Log.objects.create(user=user, log_type="CHAT", action=output)
    return Response({"output": output})


@api_view(["GET"])
def logs_view(request):
    """Return latest 50 logs."""
    logs = Log.objects.order_by("-timestamp")[:50]
    serializer = LogSerializer(logs, many=True)
    return Response(serializer.data)


@api_view(["GET"])
def log_detail_view(request, pk):
    """Fetch a single log by ID."""
    log = get_object_or_404(Log, pk=pk)
    serializer = LogSerializer(log)
    return Response(serializer.data)