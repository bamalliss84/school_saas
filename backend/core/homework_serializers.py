from datetime import datetime
from decimal import Decimal

from rest_framework import serializers

from .serializer_fields import OptionalBooleanField

from .models import (
    AcademicTerm, AcademicYear, Homework, HomeworkActionLog, HomeworkAttachment,
    HomeworkSubmission, HomeworkSubmissionAttachment, StudentEnrollment,
    TeacherAssignment,
)
from .selectors import user_can_manage_teacher_assignment
from .services.homework import create_homework, update_homework
from .services.homework_completion import completion_flags


class HomeworkQuerySerializer(serializers.Serializer):
    status = serializers.ChoiceField(required=False, choices=Homework.STATUS_CHOICES)
    academic_year_id = serializers.IntegerField(required=False, min_value=1)
    academic_term_id = serializers.IntegerField(required=False, min_value=1)
    teacher_assignment_id = serializers.IntegerField(required=False, min_value=1)
    classroom_id = serializers.IntegerField(required=False, min_value=1)
    section_id = serializers.IntegerField(required=False, min_value=1)
    subject_id = serializers.IntegerField(required=False, min_value=1)
    publish_from = serializers.DateTimeField(required=False)
    publish_to = serializers.DateTimeField(required=False)
    due_from = serializers.DateTimeField(required=False)
    due_to = serializers.DateTimeField(required=False)
    overdue = OptionalBooleanField(required=False)
    has_submission = OptionalBooleanField(required=False)
    submission_status = serializers.ChoiceField(
        required=False, choices=HomeworkSubmission.STATUS_CHOICES,
    )
    completion_status = serializers.ChoiceField(required=False, choices=(
        'not_started', 'draft', 'submitted', 'returned', 'graded', 'overdue', 'closed_without_submission',
    ))
    graded = OptionalBooleanField(required=False)
    pending_grading = OptionalBooleanField(required=False)
    search = serializers.CharField(required=False, allow_blank=True)
    ordering = serializers.ChoiceField(
        required=False, default='-created_at', choices=(
            'created_at', '-created_at', 'due_date', '-due_date',
            'publish_at', '-publish_at', 'title', '-title',
        ),
    )

    def validate(self, attrs):
        # QueryDict treats absent checkbox-like booleans as False; absence means no filter.
        for field in ('overdue', 'has_submission', 'graded', 'pending_grading'):
            if field not in self.initial_data:
                attrs.pop(field, None)
        for start, end in (('publish_from', 'publish_to'), ('due_from', 'due_to')):
            if attrs.get(start) and attrs.get(end) and attrs[start] > attrs[end]:
                raise serializers.ValidationError({end: f'Must be on or after {start}.'})
        return attrs



class HomeworkReportQuerySerializer(serializers.Serializer):
    section_id = serializers.IntegerField(required=False, min_value=1)
    academic_year_id = serializers.IntegerField(required=False, min_value=1)
    academic_term_id = serializers.IntegerField(required=False, min_value=1)
    date_from = serializers.DateTimeField(required=False)
    date_to = serializers.DateTimeField(required=False)

    def validate(self, attrs):
        if attrs.get('date_from') and attrs.get('date_to') and attrs['date_from'] > attrs['date_to']:
            raise serializers.ValidationError({'date_to': 'Must be on or after date_from.'})
        return attrs

class SubmissionQuerySerializer(serializers.Serializer):
    homework_id = serializers.IntegerField(required=False, min_value=1)
    status = serializers.ChoiceField(required=False, choices=HomeworkSubmission.STATUS_CHOICES)
    student_id = serializers.IntegerField(required=False, min_value=1)
    submitted_from = serializers.DateTimeField(required=False)
    submitted_to = serializers.DateTimeField(required=False)
    graded = OptionalBooleanField(required=False)
    late = OptionalBooleanField(required=False)
    ordering = serializers.ChoiceField(
        required=False, default='-submitted_at', choices=(
            'submitted_at', '-submitted_at', 'graded_at', '-graded_at',
            'student_enrollment__student__full_name',
            '-student_enrollment__student__full_name',
        ),
    )


class HomeworkAttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = HomeworkAttachment
        fields = ('id', 'file', 'original_name', 'content_type', 'file_size', 'uploaded_by', 'created_at')
        read_only_fields = fields


class SubmissionAttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = HomeworkSubmissionAttachment
        fields = ('id', 'file', 'original_name', 'content_type', 'file_size', 'uploaded_by', 'created_at')
        read_only_fields = fields


class HomeworkSubmissionSerializer(serializers.ModelSerializer):
    student_id = serializers.IntegerField(source='student_enrollment.student_id', read_only=True)
    student_name = serializers.CharField(source='student_enrollment.student.full_name', read_only=True)
    student_code = serializers.CharField(source='student_enrollment.student.student_code', read_only=True)
    homework_title = serializers.CharField(source='homework.title', read_only=True)
    is_late = serializers.BooleanField(read_only=True)
    can_edit = serializers.SerializerMethodField()
    can_submit = serializers.SerializerMethodField()
    can_grade = serializers.SerializerMethodField()
    attachments_count = serializers.IntegerField(source='attachments.count', read_only=True)
    attachments = SubmissionAttachmentSerializer(many=True, read_only=True)

    class Meta:
        model = HomeworkSubmission
        fields = (
            'id', 'homework', 'homework_title', 'student_enrollment', 'student_id',
            'student_name', 'student_code', 'answer', 'status', 'submitted_at',
            'grade', 'teacher_note', 'graded_by', 'graded_at', 'returned_at',
            'is_late', 'can_edit', 'can_submit', 'can_grade', 'attachments_count',
            'attachments', 'created_at', 'updated_at',
        )
        read_only_fields = (
            'id', 'homework', 'student_enrollment', 'status', 'submitted_at',
            'grade', 'teacher_note', 'graded_by', 'graded_at', 'returned_at',
            'created_at', 'updated_at',
        )

    def _owns(self, obj):
        request = self.context.get('request')
        return bool(
            request and request.user.role == 'student'
            and obj.student_enrollment.student.user_id == request.user.id
        )

    def get_can_edit(self, obj) -> bool:
        return self._owns(obj) and obj.homework.status == 'published' and obj.status in ('draft', 'returned')

    def get_can_submit(self, obj) -> bool:
        return self.get_can_edit(obj)

    def get_can_grade(self, obj) -> bool:
        request = self.context.get('request')
        return bool(
            request and obj.status == 'submitted'
            and user_can_manage_teacher_assignment(request.user, obj.homework.teacher_assignment)
            and obj.homework.max_grade is not None
        )

    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context.get('request')
        if request and request.user.role == 'parent' and instance.status not in ('graded', 'returned'):
            data['grade'] = None
            data['teacher_note'] = ''
            data['graded_at'] = None
        return data


class HomeworkSerializer(serializers.ModelSerializer):
    school = serializers.PrimaryKeyRelatedField(read_only=True)
    academic_year = serializers.PrimaryKeyRelatedField(
        queryset=AcademicYear.objects.all(), required=False,
    )
    created_by = serializers.PrimaryKeyRelatedField(read_only=True)
    classroom_id = serializers.IntegerField(source='teacher_assignment.classroom_id', read_only=True)

    section_id = serializers.IntegerField(source='teacher_assignment.section_id', read_only=True)
    subject_id = serializers.IntegerField(source='teacher_assignment.subject_id', read_only=True)
    subject_name = serializers.CharField(source='teacher_assignment.subject.name', read_only=True)
    attachments = HomeworkAttachmentSerializer(many=True, read_only=True)
    attachments_count = serializers.IntegerField(source='attachments.count', read_only=True)
    submission_status = serializers.SerializerMethodField()
    submitted_at = serializers.SerializerMethodField()
    graded_at = serializers.SerializerMethodField()
    grade = serializers.SerializerMethodField()
    teacher_note = serializers.SerializerMethodField()
    is_late = serializers.SerializerMethodField()
    can_edit = serializers.SerializerMethodField()
    can_publish = serializers.SerializerMethodField()
    can_close = serializers.SerializerMethodField()
    can_submit = serializers.SerializerMethodField()
    can_grade = serializers.SerializerMethodField()
    completion_status = serializers.SerializerMethodField()
    is_overdue = serializers.SerializerMethodField()
    can_create_draft = serializers.SerializerMethodField()
    can_final_submit = serializers.SerializerMethodField()
    submission_attachments_count = serializers.SerializerMethodField()
    teacher = serializers.CharField(source='teacher_assignment.teacher.full_name', read_only=True)
    description_preview = serializers.SerializerMethodField()

    class Meta:
        model = Homework
        fields = (
            'id', 'school', 'academic_year', 'academic_term', 'teacher_assignment',
            'classroom_id', 'section_id', 'subject_id', 'subject_name', 'title',
            'description', 'submission_type', 'status', 'publish_at', 'published_at', 'due_date',
            'max_grade', 'created_by', 'attachments', 'attachments_count',
            'submission_status', 'submitted_at', 'graded_at', 'grade',
            'teacher_note', 'is_late', 'can_edit', 'can_publish', 'can_close',
            'can_submit', 'can_grade', 'completion_status', 'is_overdue',
            'can_create_draft', 'can_final_submit', 'submission_attachments_count',
            'teacher', 'description_preview', 'created_at', 'updated_at',
        )
        read_only_fields = ('id', 'status', 'published_at', 'created_at', 'updated_at')

    def _own_submission(self, obj):
        request = self.context.get('request')
        if not request:
            return None
        active_role = getattr(request, 'active_role', None)
        if active_role == 'student':
            return next((item for item in obj.submissions.all() if item.student_enrollment.student.user_id == request.user.id), None)
        if active_role == 'parent':
            student_id = request.parser_context.get('kwargs', {}).get('student_id') if request.parser_context else None
            return next((item for item in obj.submissions.all() if item.student_enrollment.student_id == student_id), None)
        return None

    def get_submission_status(self, obj) -> str | None:
        submission = self._own_submission(obj)
        return submission.status if submission else None

    def get_submitted_at(self, obj) -> datetime | None:
        submission = self._own_submission(obj)
        return submission.submitted_at if submission else None

    def get_graded_at(self, obj) -> datetime | None:
        submission = self._own_submission(obj)
        return submission.graded_at if submission else None

    def get_grade(self, obj) -> Decimal | None:
        submission = self._own_submission(obj)
        return submission.grade if submission else None

    def get_teacher_note(self, obj) -> str | None:
        submission = self._own_submission(obj)
        return submission.teacher_note if submission else None

    def get_is_late(self, obj) -> bool:
        submission = self._own_submission(obj)
        return submission.is_late if submission else False

    def _can_manage(self, obj):
        request = self.context.get('request')
        return bool(request and user_can_manage_teacher_assignment(request.user, obj.teacher_assignment))

    def get_can_edit(self, obj) -> bool:
        return self._can_manage(obj) and obj.status == 'draft'

    def get_can_publish(self, obj) -> bool:
        return self.get_can_edit(obj)

    def get_can_close(self, obj) -> bool:
        return self._can_manage(obj) and obj.status == 'published'

    def get_can_submit(self, obj) -> bool:
        request = self.context.get('request')
        return bool(
            request and request.user.role == 'student'
            and obj.status == 'published' and obj.submission_type != 'none'
        )

    def _completion(self, obj):
        request = self.context.get('request')
        membership = getattr(request, 'active_membership', None) if request else None
        return completion_flags(obj, self._own_submission(obj), writable=bool(membership and membership.can_write))

    def get_completion_status(self, obj) -> str:
        return self._completion(obj)['completion_status']

    def get_is_overdue(self, obj) -> bool:
        return self._completion(obj)['is_overdue']

    def get_can_create_draft(self, obj) -> bool:
        return self._completion(obj)['can_create_draft']

    def get_can_final_submit(self, obj) -> bool:
        return self._completion(obj)['can_final_submit']

    def get_submission_attachments_count(self, obj) -> int:
        submission = self._own_submission(obj)
        return submission.attachments.count() if submission else 0

    def get_description_preview(self, obj) -> str:
        return obj.description[:160]

    def get_can_grade(self, obj) -> bool:
        return self._can_manage(obj) and obj.max_grade is not None

    def validate(self, attrs):
        request = self.context['request']
        from .context import require_writable_context
        require_writable_context(request)

        assignment = attrs.get('teacher_assignment', getattr(self.instance, 'teacher_assignment', None))
        year = attrs.get('academic_year', getattr(self.instance, 'academic_year', None))
        if assignment and not year:
            year = assignment.academic_year
            attrs['academic_year'] = year
        term = attrs.get('academic_term', getattr(self.instance, 'academic_term', None))
        if not assignment or not year or not term:
            raise serializers.ValidationError('Homework relationships are required.')
        if not user_can_manage_teacher_assignment(request.user, assignment, request=request):
            raise serializers.ValidationError('Teacher assignment is outside your scope.')
        if (
            assignment.academic_year_id != year.pk
            or term.school_id != assignment.school_id
            or term.academic_year_id != year.pk
            or not assignment.is_current
        ):
            raise serializers.ValidationError('Invalid homework relationships.')
        due_date = attrs.get('due_date', getattr(self.instance, 'due_date', None))
        publish_at = attrs.get('publish_at', getattr(self.instance, 'publish_at', None))
        if publish_at and due_date and due_date < publish_at:
            raise serializers.ValidationError({'due_date': 'Due date cannot precede publish time.'})
        return attrs


    def create(self, validated_data):
        return create_homework(
            actor=self.context['request'].user,
            request=self.context['request'],
            **validated_data,
        )

    def update(self, instance, validated_data):
        return update_homework(
            homework=instance, actor=self.context['request'].user,
            request=self.context['request'], **validated_data,
        )


class BulkHomeworkSerializer(serializers.Serializer):
    homework_ids = serializers.ListField(
        child=serializers.IntegerField(min_value=1), allow_empty=False,
    )

    def validate_homework_ids(self, value):
        if len(value) != len(set(value)):
            raise serializers.ValidationError('Duplicate homework IDs are not allowed.')
        return value


class SubmissionAnswerSerializer(serializers.Serializer):
    answer = serializers.CharField(required=False, allow_blank=True, default='')


class ReturnSubmissionSerializer(serializers.Serializer):
    teacher_note = serializers.CharField(required=False, allow_blank=True, default='')


class GradeSubmissionSerializer(ReturnSubmissionSerializer):
    grade = serializers.DecimalField(max_digits=7, decimal_places=2)


class HomeworkBulkGradeItemSerializer(GradeSubmissionSerializer):
    submission_id = serializers.IntegerField(min_value=1)


class BulkGradeSubmissionsSerializer(serializers.Serializer):
    items = HomeworkBulkGradeItemSerializer(many=True, allow_empty=False)

    def validate_items(self, value):
        ids = [item['submission_id'] for item in value]
        if len(ids) != len(set(ids)):
            raise serializers.ValidationError('Duplicate submissions are not allowed.')
        return value


class AttachmentUploadSerializer(serializers.Serializer):
    files = serializers.ListField(
        child=serializers.FileField(), allow_empty=False,
    )


class HomeworkActionLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = HomeworkActionLog
        fields = (
            'id', 'school', 'actor', 'action', 'entity_type', 'entity_id',
            'old_data', 'new_data', 'reason', 'request_id', 'ip_address',
            'user_agent', 'created_at',
        )
        read_only_fields = fields