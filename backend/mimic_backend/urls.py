from django.contrib import admin
from django.urls import path, include
from rest_framework import routers
from main.views import (
    TaskViewSet,
    LogViewSet,
    agent_view,
    logs_view,
    log_detail_view,
    home,
)

router = routers.DefaultRouter()
router.register(r'tasks', TaskViewSet, basename="task")
router.register(r'logs', LogViewSet, basename="log")

urlpatterns = [
    path('', home, name="home"),
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),  # /api/tasks/ and /api/logs/
    path('api/agent/', agent_view, name="agent"),  # POST endpoint
    path('api/logs-latest/', logs_view, name="logs-latest"),  # latest logs only
    path('api/logs/<int:pk>/', log_detail_view, name="log-detail"),  # ✅ now valid
]