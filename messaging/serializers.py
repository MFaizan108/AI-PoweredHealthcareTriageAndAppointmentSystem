from rest_framework import serializers

from accounts.serializers import UserSerializer

from .models import Message


class MessageSerializer(serializers.ModelSerializer):
    sender_detail = UserSerializer(source="sender", read_only=True)

    class Meta:
        model = Message
        fields = ["id", "appointment", "sender", "sender_detail", "recipient", "body", "attachment", "is_read", "created_at"]
        read_only_fields = ["id", "sender", "recipient", "is_read", "created_at"]

    def validate_body(self, value):
        return value

    def validate(self, attrs):
        if not attrs.get("body") and not self.initial_data.get("attachment"):
            raise serializers.ValidationError("Message must have a body or an attachment.")
        return attrs
