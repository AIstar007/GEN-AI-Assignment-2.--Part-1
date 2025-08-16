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