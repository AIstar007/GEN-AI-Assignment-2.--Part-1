from django.db import models
from django.utils import timezone


class Task(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title


class Log(models.Model):
    LOG_TYPES = [
        ("install", "Application Install"),
        ("chat", "Chat Message"),
        ("file", "File Download"),
        ("system", "System Event"),
    ]

    user = models.CharField(max_length=50)  # could be replaced with ForeignKey to auth.User later
    action = models.TextField()
    log_type = models.CharField(max_length=20, choices=LOG_TYPES, default="chat")
    timestamp = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"[{self.log_type.upper()}] {self.user} @ {self.timestamp:%Y-%m-%d %H:%M} - {self.action[:40]}"


class AppRequest(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
    ]

    app_name = models.CharField(max_length=100)
    version = models.CharField(max_length=50, default="latest")
    requested_by = models.CharField(max_length=100)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    eligibility = models.BooleanField(default=False)  # Admin decides
    created_at = models.DateTimeField(auto_now_add=True)
    decided_at = models.DateTimeField(null=True, blank=True)
    note = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.app_name} {self.version} - {self.status}"
