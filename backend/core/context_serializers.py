from django.db import transaction
from django.utils import timezone
from rest_framework import serializers

from .context import _academic_year_for_membership, get_user_memberships
from .models import HomeworkActionLog, SchoolMembership
from .services.exam_results import request_audit_metadata


class SchoolMembershipSerializer(serializers.ModelSerializer):
    school = serializers.SerializerMethodField()
    academic_year = serializers.SerializerMethodField()
    access_mode = serializers.SerializerMethodField()
    membership_id = serializers.IntegerField(source='pk', read_only=True)
    can_write = serializers.SerializerMethodField()
    is_current_school = serializers.SerializerMethodField()
    unread_notifications_count = serializers.SerializerMethodField()
    unread_conversations_count = serializers.SerializerMethodField()

    class Meta:
        model = SchoolMembership
        fields = (
            'membership_id', 'school', 'role', 'status', 'access_mode',
            'is_default', 'is_current_school', 'academic_year', 'can_write',
            'start_date', 'end_date', 'last_used_at', 'unread_notifications_count',
            'unread_conversations_count',
        )
        read_only_fields = fields

    def get_school(self, obj) -> dict:
        return {'id': obj.school_id, 'name': obj.school.name}

    def get_academic_year(self, obj) -> dict | None:
        year_map = self.context.get('academic_year_map')
        if year_map is not None:
            return year_map.get(obj.pk)
        request = self.context.get('request')
        if request is None:
            year = obj.school.academic_years.filter(is_active=True).order_by('-start_date').first()
        else:
            year = _academic_year_for_membership(obj, request)
        return {'id': year.pk, 'name': year.name} if year else None

    def get_access_mode(self, obj) -> str:
        return obj.access_mode

    def get_can_write(self, obj) -> bool:
        return obj.can_write

    def get_unread_notifications_count(self, obj) -> int:
        counts = self.context.get('notification_counts')
        return counts.get(obj.pk, 0) if counts is not None else obj.notifications.filter(is_read=False).count()

    def get_unread_conversations_count(self, obj) -> int:
        counts = self.context.get('conversation_counts')
        if counts is not None:
            return counts.get(obj.pk, 0)
        from .services.messaging import get_context_unread_conversation_counts
        return get_context_unread_conversation_counts([obj]).get(obj.pk, 0)

    def get_is_current_school(self, obj) -> bool:
        user = obj.user
        if obj.role == 'student' and hasattr(user, 'student_profile'):
            return user.student_profile.enrollments.filter(
                school_id=obj.school_id, is_current=True, status='active',
            ).exists()
        return obj.status == 'active'


class ContextListSerializer(serializers.Serializer):
    current_context = SchoolMembershipSerializer(allow_null=True)
    contexts = SchoolMembershipSerializer(many=True)


class DefaultContextSerializer(serializers.Serializer):
    membership_id = serializers.IntegerField(min_value=1)

    def validate_membership_id(self, value):
        request = self.context['request']
        membership = get_user_memberships(request.user, include_ended=True).filter(pk=value).first()
        if membership is None:
            raise serializers.ValidationError('School context was not found.')
        if membership.status != 'active' or not membership.school.is_active:
            raise serializers.ValidationError('Only an active context can be default.')
        self.membership = membership
        return value

    @transaction.atomic
    def save(self):
        request = self.context['request']
        SchoolMembership.objects.select_for_update().filter(user=request.user).update(is_default=False)
        membership = SchoolMembership.objects.select_for_update().get(pk=self.membership.pk)
        membership.is_default = True
        membership.last_used_at = timezone.now()
        membership.save(update_fields=('is_default', 'last_used_at', 'updated_at'))
        HomeworkActionLog.objects.create(
            school=membership.school,
            actor=request.user,
            action='default_membership_change',
            entity_type='school_membership',
            entity_id=membership.pk,
            new_data={'membership_id': membership.pk, 'role': membership.role},
            **request_audit_metadata(request),
        )
        return membership