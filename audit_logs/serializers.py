from rest_framework import serializers

from .models import AuditLog


class AuditLogSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True, default="")

    class Meta:
        model = AuditLog
        fields = [
            "id", "user", "username", "username_attempted", "action", "method",
            "path", "object_id", "changes", "status_code", "ip_address", "user_agent", "created_at",
        ]
        read_only_fields = fields
