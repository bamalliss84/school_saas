from rest_framework import serializers
from .models import Notification


class NotificationQuerySerializer(serializers.Serializer):
    is_read = serializers.BooleanField(required=False)
    notification_type = serializers.ChoiceField(choices=Notification.TYPE_CHOICES, required=False)
    date_from = serializers.DateTimeField(required=False)
    date_to = serializers.DateTimeField(required=False)
    source_type = serializers.CharField(max_length=50, required=False)
    ordering = serializers.ChoiceField(choices=('created_at', '-created_at'), default='-created_at')

    def validate(self, attrs):
        if attrs.get('date_from') and attrs.get('date_to') and attrs['date_from'] > attrs['date_to']:
            raise serializers.ValidationError('date_from must not follow date_to.')
        return attrs


class NotificationSerializer(serializers.ModelSerializer):
    action = serializers.SerializerMethodField()
    school = serializers.SerializerMethodField()
    membership_id = serializers.IntegerField(source='recipient_membership_id', read_only=True)

    class Meta:
        model = Notification
        fields = ('id', 'notification_type', 'title', 'body', 'is_read', 'read_at', 'created_at', 'action', 'school', 'membership_id', 'payload')
        read_only_fields = fields

    def get_action(self, obj) -> dict | None:
        action = obj.payload.get('action') if isinstance(obj.payload, dict) else None
        return action if isinstance(action, dict) else None

    def get_school(self, obj) -> dict:
        return {'id': obj.school_id, 'name': obj.school.name}


class NotificationReadAllSerializer(serializers.Serializer):
    updated_count = serializers.IntegerField(read_only=True)


class NotificationUnreadSerializer(serializers.Serializer):
    membership_id = serializers.IntegerField()
    unread_count = serializers.IntegerField()