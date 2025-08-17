from rest_framework import serializers
from .models import Task, Log, AppRequest


class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = "__all__"


class LogSerializer(serializers.ModelSerializer):
    class Meta:
        model = Log
        fields = "__all__"


class AppRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = AppRequest
        fields = "__all__"
