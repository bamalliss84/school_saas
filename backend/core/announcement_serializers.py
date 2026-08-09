from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from .serializer_fields import OptionalBooleanField

from .models import Announcement, AnnouncementAttachment, AnnouncementReceipt
from .services.announcements import create_announcement, update_announcement


class AnnouncementQuerySerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=Announcement.STATUS_CHOICES, required=False)
    priority = serializers.ChoiceField(choices=Announcement.PRIORITY_CHOICES, required=False)
    audience_type = serializers.ChoiceField(choices=Announcement.AUDIENCE_CHOICES, required=False)
    academic_year_id = serializers.IntegerField(min_value=1, required=False)
    unread = OptionalBooleanField(required=False)
    published_from = serializers.DateTimeField(required=False)
    published_to = serializers.DateTimeField(required=False)
    search = serializers.CharField(required=False, allow_blank=True, max_length=200)
    ordering = serializers.ChoiceField(
        choices=('published_at', '-published_at', 'created_at', '-created_at', 'priority', '-priority'),
        default='-published_at',
    )

    def validate(self, attrs):
        if attrs.get('published_from') and attrs.get('published_to') and attrs['published_from'] > attrs['published_to']:
            raise serializers.ValidationError('published_from must not follow published_to.')
        return attrs


class AnnouncementAttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnnouncementAttachment
        fields = ('id', 'file', 'original_name', 'content_type', 'file_size', 'created_at')
        read_only_fields = fields


class AnnouncementWriteSerializer(serializers.ModelSerializer):
    target_student_ids = serializers.ListField(
        child=serializers.IntegerField(min_value=1), required=False, write_only=True,
    )

    class Meta:
        model = Announcement
        fields = (
            'academic_year', 'title', 'body', 'priority', 'audience_type', 'target_roles',
            'classroom', 'section', 'teacher_assignment', 'target_student_ids',
            'include_parents', 'allow_inquiry',
        )

    def create(self, validated_data):
        student_ids = validated_data.pop('target_student_ids', ())
        request = self.context['request']
        return create_announcement(
            membership=request.active_membership,
            request=request,
            target_student_ids=student_ids,
            **validated_data,
        )

    def update(self, instance, validated_data):
        student_ids = validated_data.pop('target_student_ids', None)
        request = self.context['request']
        return update_announcement(
            announcement=instance,
            membership=request.active_membership,
            request=request,
            target_student_ids=student_ids,
            **validated_data,
        )


class AnnouncementSerializer(serializers.ModelSerializer):
    attachments = AnnouncementAttachmentSerializer(many=True, read_only=True)
    school = serializers.SerializerMethodField()
    academic_year = serializers.SerializerMethodField()
    classroom = serializers.SerializerMethodField()
    section = serializers.SerializerMethodField()
    teacher_assignment = serializers.SerializerMethodField()
    created_by = serializers.SerializerMethodField()
    published_by = serializers.SerializerMethodField()
    receipt = serializers.SerializerMethodField()
    permissions = serializers.SerializerMethodField()
    target_student_ids = serializers.SerializerMethodField()

    class Meta:
        model = Announcement
        fields = (
            'id', 'school', 'academic_year', 'title', 'body', 'status', 'priority',
            'audience_type', 'target_roles', 'classroom', 'section', 'teacher_assignment',
            'target_student_ids', 'include_parents', 'allow_inquiry', 'attachments',
            'created_by', 'published_by', 'published_at', 'closed_at', 'archived_at',
            'created_at', 'updated_at', 'receipt', 'permissions',
        )
        read_only_fields = fields

    @extend_schema_field(OpenApiTypes.OBJECT)
    def get_school(self, obj):
        return {'id': obj.school_id, 'name': obj.school.name}

    @extend_schema_field(OpenApiTypes.OBJECT)
    def get_academic_year(self, obj):
        return {'id': obj.academic_year_id, 'name': obj.academic_year.name} if obj.academic_year_id else None

    @extend_schema_field(OpenApiTypes.OBJECT)
    def get_classroom(self, obj):
        return {'id': obj.classroom_id, 'name': obj.classroom.name} if obj.classroom_id else None

    @extend_schema_field(OpenApiTypes.OBJECT)
    def get_section(self, obj):
        return {'id': obj.section_id, 'name': obj.section.name} if obj.section_id else None

    @extend_schema_field(OpenApiTypes.OBJECT)
    def get_teacher_assignment(self, obj):
        if not obj.teacher_assignment_id:
            return None
        assignment = obj.teacher_assignment
        return {
            'id': assignment.pk,
            'subject': {'id': assignment.subject_id, 'name': assignment.subject.name},
        }

    @extend_schema_field(OpenApiTypes.OBJECT)
    def get_created_by(self, obj):
        membership = obj.created_by_membership
        return {'membership_id': membership.pk, 'name': membership.user.get_full_name() or membership.user.username, 'role': membership.role}

    @extend_schema_field(OpenApiTypes.OBJECT)
    def get_published_by(self, obj):
        membership = obj.published_by_membership
        if not membership:
            return None
        return {'membership_id': membership.pk, 'name': membership.user.get_full_name() or membership.user.username}

    @extend_schema_field(OpenApiTypes.OBJECT)
    def get_receipt(self, obj):
        request = self.context.get('request')
        membership = getattr(request, 'active_membership', None) if request else None
        if not membership:
            return None
        prefetched = getattr(obj, '_context_receipts', None)
        if prefetched is not None:
            receipt = next((row for row in prefetched if row.recipient_membership_id == membership.pk), None)
        else:
            receipt = AnnouncementReceipt.objects.filter(announcement=obj, recipient_membership=membership).first()
        return {'is_read': bool(receipt and receipt.read_at), 'read_at': receipt.read_at if receipt else None} if receipt else None

    @extend_schema_field(OpenApiTypes.OBJECT)
    def get_permissions(self, obj):
        request = self.context.get('request')
        membership = getattr(request, 'active_membership', None) if request else None
        active = bool(membership and membership.status == 'active')
        manager = bool(active and (
            membership.role in ('super_admin', 'school_admin')
            or (membership.role == 'teacher' and obj.created_by_membership_id == membership.pk)
        ))
        prefetched_receipts = getattr(obj, '_context_receipts', None)
        has_receipt = False
        if membership:
            has_receipt = (
                bool(prefetched_receipts) if prefetched_receipts is not None
                else AnnouncementReceipt.objects.filter(announcement=obj, recipient_membership=membership).exists()
            )
        return {
            'can_edit': manager and obj.status == 'draft',
            'can_publish': manager and obj.status == 'draft',
            'can_close': manager and obj.status == 'published',
            'can_archive': manager and obj.status in ('published', 'closed'),
            'can_inquire': (
                active and has_receipt and membership.role in ('student', 'parent', 'teacher')
                and obj.allow_inquiry and obj.status in ('published', 'closed')
            ),
        }

    @extend_schema_field({"type": "array", "items": {"type": "integer"}})
    def get_target_student_ids(self, obj):
        request = self.context.get('request')
        membership = getattr(request, 'active_membership', None) if request else None
        if membership and membership.status == 'active' and (
            membership.role in ('super_admin', 'school_admin')
            or obj.created_by_membership_id == membership.pk
        ):
            return [student.pk for student in obj.target_students.all()]
        return []




class AnnouncementInquirySerializer(serializers.Serializer):
    student_id = serializers.IntegerField(min_value=1, required=False)

class AnnouncementReceiptSerializer(serializers.Serializer):
    announcement_id = serializers.IntegerField()
    is_read = serializers.BooleanField()
    read_at = serializers.DateTimeField(allow_null=True)




class AnnouncementTargetPreviewSerializer(serializers.Serializer):
    announcement_id = serializers.IntegerField()
    eligible_count = serializers.IntegerField()
    by_role = serializers.DictField(child=serializers.IntegerField())

class AnnouncementSummarySerializer(serializers.Serializer):
    announcement_id = serializers.IntegerField()
    delivered_count = serializers.IntegerField()
    read_count = serializers.IntegerField()
    unread_count = serializers.IntegerField()
    read_rate = serializers.FloatField()
    by_role = serializers.DictField(child=serializers.DictField())
