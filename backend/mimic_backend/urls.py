from django.contrib import admin
from django.urls import path, include
from rest_framework import routers
from main.views import (
    TaskViewSet,
    LogViewSet,
    AppRequestViewSet,   
    agent_view,
    logs_view,
    log_detail_view,
    home,
)

router = routers.DefaultRouter()
router.register(r'tasks', TaskViewSet, basename="task")
router.register(r'logs', LogViewSet, basename="log")
router.register(r'app-requests', AppRequestViewSet, basename="app-request")  

urlpatterns = [
    path('', home, name="home"),
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),  # /api/tasks/, /api/logs/, /api/app-requests/
    path('api/agent/', agent_view, name="agent"),  # POST endpoint
    path('api/logs-latest/', logs_view, name="logs-latest"),  # latest logs only
    path('api/logs/<int:pk>/', log_detail_view, name="log-detail"),  # ✅ single log
]
