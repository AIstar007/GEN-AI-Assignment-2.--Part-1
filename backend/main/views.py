from rest_framework import viewsets
from rest_framework.decorators import api_view, action
from rest_framework.response import Response
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from .models import Task, Log, AppRequest
from .serializers import TaskSerializer, LogSerializer, AppRequestSerializer
import re


# ----------------- VIEWSETS ----------------- #
class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer


class LogViewSet(viewsets.ModelViewSet):
    queryset = Log.objects.all().order_by("-timestamp")
    serializer_class = LogSerializer


class AppRequestViewSet(viewsets.ModelViewSet):
    """Admin + User requests for apps"""
    queryset = AppRequest.objects.all().order_by("-created_at")
    serializer_class = AppRequestSerializer

    # Custom endpoint → Approve
    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        app_req = self.get_object()
        app_req.status = "approved"
        app_req.eligibility = True
        app_req.save()

        Log.objects.create(
            user=request.data.get("admin", "admin"),
            log_type="system",
            action=f"✅ Approved {app_req.app_name} v{app_req.version}",
        )
        return Response({"message": f"{app_req.app_name} v{app_req.version} approved."})

    # Custom endpoint → Reject
    @action(detail=True, methods=["post"])
    def reject(self, request, pk=None):
        app_req = self.get_object()
        app_req.status = "rejected"
        app_req.eligibility = False
        app_req.save()

        Log.objects.create(
            user=request.data.get("admin", "admin"),
            log_type="system",
            action=f"❌ Rejected {app_req.app_name} v{app_req.version}",
        )
        return Response({"message": f"{app_req.app_name} v{app_req.version} rejected."})


# ----------------- SIMPLE VIEWS ----------------- #
def home(request):
    return HttpResponse("Hello 👋, Django API is running! Go to /api/tasks/")


@api_view(["POST"])
def agent_view(request):
    """Agent endpoint: handles install/download commands and logs requests for approval."""
    user_input = request.data.get("input", "")
    user = request.data.get("user", "demo")

    # Detect install or download
    m = re.match(r".*(install|download)\s+(?P<app>[A-Za-z0-9_\-]+)\s*(?P<version>[\d\.]*)", user_input, re.I)
    if m:
        action_type = m.group(1).lower()
        app = m.group("app")
        version = m.group("version") or "latest"

        # Create AppRequest (pending approval)
        app_req = AppRequest.objects.create(
            app_name=app,
            version=version,
            requested_by=user,
            status="pending",
            eligibility=False
        )

        message = f"📌 Request created for {app} v{version}. Waiting for admin approval."
        Log.objects.create(user=user, log_type="install" if action_type == "install" else "file", action=message)

        return Response({
            "message": message,
            "request_id": app_req.id,
            "status": app_req.status,
            "eligibility": app_req.eligibility
        })

    # Otherwise → fallback chat
    output = f"🤖 You said: {user_input}"
    Log.objects.create(user=user, log_type="chat", action=output)
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
