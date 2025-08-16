from django.contrib import admin
from import_export.admin import ExportMixin
from .models import Task, Log


class TaskAdmin(ExportMixin, admin.ModelAdmin):
    list_display = ("id", "title", "completed", "created_at", "updated_at")
    list_filter = ("completed", "created_at", "updated_at")
    search_fields = ("title", "description")
    ordering = ("-created_at",)


class LogAdmin(ExportMixin, admin.ModelAdmin):
    list_display = ("id", "user", "log_type", "action", "timestamp")
    list_filter = ("user", "log_type", "timestamp")
    search_fields = ("user", "action")
    ordering = ("-timestamp",)


admin.site.register(Task, TaskAdmin)
admin.site.register(Log, LogAdmin)