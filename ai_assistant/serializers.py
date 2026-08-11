from rest_framework import serializers

from .models import AssistantQueryLog, HospitalFAQ


class AskSerializer(serializers.Serializer):
    message = serializers.CharField()


class AssistantResponseSerializer(serializers.Serializer):
    response = serializers.CharField()
    provider_used = serializers.CharField(allow_blank=True)
    error = serializers.CharField(allow_blank=True, required=False)


class HospitalFAQSerializer(serializers.ModelSerializer):
    class Meta:
        model = HospitalFAQ
        fields = ["id", "question", "answer", "is_active"]
        read_only_fields = ["id"]


class AssistantQueryLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AssistantQueryLog
        fields = ["id", "message", "response", "provider_used", "created_at"]
        read_only_fields = fields
