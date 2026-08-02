from rest_framework import serializers

from .models import Conversation, Message, MessageAttachment


class ConversationStartSerializer(serializers.Serializer):
    conversation_type = serializers.ChoiceField(choices=Conversation.TYPE_CHOICES)
    subject = serializers.CharField(max_length=200)
    teacher_assignment_id = serializers.IntegerField(required=False, min_value=1)
    student_id = serializers.IntegerField(required=False, min_value=1)
    homework_id = serializers.IntegerField(required=False, min_value=1)
    parent_membership_id = serializers.IntegerField(required=False, min_value=1)
    parent_id = serializers.IntegerField(required=False, min_value=1)
    category = serializers.ChoiceField(
        choices=Conversation.CATEGORY_CHOICES, required=False, allow_blank=True,
    )
    priority = serializers.ChoiceField(
        choices=Conversation.PRIORITY_CHOICES, required=False, default='normal',
    )

    def validate(self, attrs):
        kind = attrs['conversation_type']
        request = self.context.get('request')
        role = getattr(request, 'active_role', None)
        if kind in ('teacher_student', 'teacher_parent') and not attrs.get('teacher_assignment_id'):
            raise serializers.ValidationError(
                {'teacher_assignment_id': 'A teacher assignment is required.'},
            )
        if kind in ('teacher_student', 'teacher_parent') and not attrs.get('student_id'):
            if not (kind == 'teacher_student' and role == 'student'):
                raise serializers.ValidationError({'student_id': 'A student is required.'})
        if kind == 'teacher_parent':
            has_parent = attrs.get('parent_membership_id') or attrs.get('parent_id')
            if role == 'teacher' and not has_parent:
                raise serializers.ValidationError(
                    {'parent_membership_id': 'A single parent recipient is required.'},
                )
            if role == 'parent' and has_parent:
                raise serializers.ValidationError(
                    {'parent_membership_id': 'Parents cannot select another parent.'},
                )
        if kind == 'homework_discussion':
            if not attrs.get('homework_id'):
                raise serializers.ValidationError({'homework_id': 'A homework item is required.'})
            if role in ('teacher', 'parent') and not attrs.get('student_id'):
                raise serializers.ValidationError({'student_id': 'A student is required.'})
        if kind == 'school_support' and not attrs.get('category'):
            attrs['category'] = 'other'
        return attrs


class MessageSerializer(serializers.ModelSerializer):
    sender = serializers.SerializerMethodField()
    attachments_count = serializers.IntegerField(source='attachments.count', read_only=True)

    class Meta:
        model = Message
        fields = (
            'id', 'conversation', 'sender', 'body', 'reply_to', 'message_type',
            'created_at', 'edited_at', 'is_deleted', 'attachments_count',
        )
        read_only_fields = fields

    def get_sender(self, obj) -> dict:
        user = obj.sender_membership.user
        return {'role': obj.sender_membership.role, 'display_name': user.get_full_name() or user.username}


class ConversationSerializer(serializers.ModelSerializer):
    participants_summary = serializers.SerializerMethodField()
    last_message_preview = serializers.SerializerMethodField()
    unread_messages_count = serializers.IntegerField(read_only=True, default=0)
    can_reply = serializers.SerializerMethodField()
    can_close = serializers.SerializerMethodField()
    can_reopen = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = (
            'id', 'conversation_type', 'subject', 'status', 'category', 'priority',
            'participants_summary', 'last_message_preview', 'last_message_at',
            'unread_messages_count', 'related_type', 'related_id', 'can_reply',
            'can_close', 'can_reopen', 'created_at', 'updated_at',
        )
        read_only_fields = fields

    def _membership(self):
        return self.context['request'].active_membership

    def get_participants_summary(self, obj) -> list:
        return [
            {'role': item.participant_role, 'display_name': item.membership.user.get_full_name() or item.membership.user.username}
            for item in obj.participants.all() if item.is_active
        ]

    def get_last_message_preview(self, obj) -> str:
        message = next(iter(getattr(obj, '_last_messages', [])), None)
        return message.body[:120] if message and not message.is_deleted else ''

    def get_can_reply(self, obj) -> bool:
        membership = self._membership()
        participant = any(
            item.membership_id == membership.pk and item.is_active and item.can_reply
            for item in obj.participants.all()
        )
        support_admin = membership.role == 'school_admin' and obj.conversation_type == 'school_support'
        return membership.can_write and obj.status in ('open', 'in_progress') and (participant or support_admin)

    def get_can_close(self, obj) -> bool:
        membership = self._membership()
        return membership.can_write and obj.status != 'closed' and (
            membership.role == 'school_admin' or obj.created_by_membership_id == membership.pk
        )

    def get_can_reopen(self, obj) -> bool:
        membership = self._membership()
        return membership.can_write and obj.status == 'closed' and (
            membership.role == 'school_admin' or obj.created_by_membership_id == membership.pk
        )


class MessageCreateSerializer(serializers.Serializer):
    body = serializers.CharField(max_length=4000, trim_whitespace=True)
    reply_to_id = serializers.IntegerField(required=False, min_value=1)


class ConversationQuerySerializer(serializers.Serializer):
    conversation_type = serializers.ChoiceField(choices=Conversation.TYPE_CHOICES, required=False)
    status = serializers.ChoiceField(choices=Conversation.STATUS_CHOICES, required=False)
    unread_only = serializers.BooleanField(required=False)
    related_homework_id = serializers.IntegerField(required=False, min_value=1)
    student_id = serializers.IntegerField(required=False, min_value=1)
    category = serializers.ChoiceField(choices=Conversation.CATEGORY_CHOICES, required=False)
    assigned_to_me = serializers.BooleanField(required=False)
    updated_from = serializers.DateTimeField(required=False)
    updated_to = serializers.DateTimeField(required=False)
    search = serializers.CharField(required=False, allow_blank=True, max_length=100)
    ordering = serializers.ChoiceField(
        choices=('-last_message_at', 'last_message_at'), default='-last_message_at',
    )


class MessageAttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = MessageAttachment
        fields = ('id', 'original_name', 'content_type', 'file_size', 'created_at')
        read_only_fields = fields
