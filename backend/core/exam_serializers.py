from django.db import transaction
from rest_framework import serializers

from .serializer_fields import OptionalBooleanField

from .exam_selectors import exams_for_user
from .models import (
    Exam, ExamResult, ExamResultLog, ExamType, School, StudentEnrollment,
)
from .selectors import get_accessible_student_enrollments_for_user
from .selectors import user_can_manage_teacher_assignment
from .services.exam_results import create_exam_result, update_exam_result


class ExamTypeQuerySerializer(serializers.Serializer):
    is_active = OptionalBooleanField(required=False)


class ExamQuerySerializer(serializers.Serializer):
    academic_year_id = serializers.IntegerField(required=False, min_value=1)
    academic_term_id = serializers.IntegerField(required=False, min_value=1)
    teacher_assignment_id = serializers.IntegerField(required=False, min_value=1)
    exam_type_id = serializers.IntegerField(required=False, min_value=1)
    status = serializers.ChoiceField(required=False, choices=Exam.STATUS_CHOICES)


class ExamResultQuerySerializer(serializers.Serializer):
    exam_id = serializers.IntegerField(required=False, min_value=1)
    student_id = serializers.IntegerField(required=False, min_value=1)
    classroom_id = serializers.IntegerField(required=False, min_value=1)
    section_id = serializers.IntegerField(required=False, min_value=1)
    subject_id = serializers.IntegerField(required=False, min_value=1)
    workflow_status = serializers.ChoiceField(
        required=False, choices=ExamResult.WORKFLOW_CHOICES,
    )
    status = serializers.ChoiceField(required=False, choices=ExamResult.STATUS_CHOICES)

class ExamTypeSerializer(serializers.ModelSerializer):
    school = serializers.PrimaryKeyRelatedField(queryset=School.objects.all(), required=False)

    class Meta:
        model = ExamType
        fields = ('id', 'school', 'name', 'code', 'max_score', 'weight_percentage', 'is_active')
        read_only_fields = ('id',)
        validators = []

    def validate(self, attrs):
        request = self.context['request']
        user = request.user
        from .context import require_writable_context
        require_writable_context(request)
        if request.active_role != 'super_admin':
            attrs['school'] = request.active_school
        elif not attrs.get('school') and not self.instance:
            raise serializers.ValidationError({'school': 'This field is required.'})
        school = attrs.get('school', getattr(self.instance, 'school', None))
        code = attrs.get('code', getattr(self.instance, 'code', None))
        duplicate = ExamType.objects.filter(school=school, code=code)
        if self.instance:
            duplicate = duplicate.exclude(pk=self.instance.pk)
        if duplicate.exists():
            raise serializers.ValidationError({'code': 'Code already exists in this school.'})
        if attrs.get('max_score', getattr(self.instance, 'max_score', 1)) <= 0:
            raise serializers.ValidationError({'max_score': 'Must be greater than zero.'})
        weight = attrs.get('weight_percentage', getattr(self.instance, 'weight_percentage', 0))
        if weight < 0 or weight > 100:
            raise serializers.ValidationError({'weight_percentage': 'Must be between 0 and 100.'})
        return attrs


class ExamSerializer(serializers.ModelSerializer):
    school = serializers.PrimaryKeyRelatedField(read_only=True)
    created_by = serializers.PrimaryKeyRelatedField(read_only=True)
    classroom_id = serializers.IntegerField(source='teacher_assignment.classroom_id', read_only=True)
    section_id = serializers.IntegerField(source='teacher_assignment.section_id', read_only=True)
    subject_id = serializers.IntegerField(source='teacher_assignment.subject_id', read_only=True)

    class Meta:
        model = Exam
        fields = (
            'id', 'school', 'academic_year', 'academic_term', 'teacher_assignment',
            'exam_type', 'created_by', 'title', 'exam_date', 'total_marks',
            'status', 'notes', 'classroom_id', 'section_id', 'subject_id', 'created_at',
        )
        read_only_fields = ('id', 'created_at')

    def validate(self, attrs):
        request = self.context['request']
        from .context import require_writable_context
        require_writable_context(request)
        assignment = attrs.get('teacher_assignment', getattr(self.instance, 'teacher_assignment', None))
        year = attrs.get('academic_year', getattr(self.instance, 'academic_year', None))
        term = attrs.get('academic_term', getattr(self.instance, 'academic_term', None))
        exam_type = attrs.get('exam_type', getattr(self.instance, 'exam_type', None))
        if not user_can_manage_teacher_assignment(request.user, assignment, request=request):
            raise serializers.ValidationError('Teacher assignment is outside your scope.')
        if request.active_role != 'super_admin' and assignment.school_id != request.active_school.id:
            raise serializers.ValidationError('Invalid exam relationships.')
        if (
            request.active_academic_year is None
            or assignment.academic_year_id != request.active_academic_year.id
        ):
            raise serializers.ValidationError('Teacher assignment is outside the active academic year.')
        if (
            assignment.academic_year_id != year.id
            or term.school_id != assignment.school_id
            or term.academic_year_id != year.id
            or exam_type.school_id != assignment.school_id
        ):
            raise serializers.ValidationError('Invalid exam relationships.')
        attrs['school'] = assignment.school
        if self.instance is None:
            attrs['status'] = 'draft'
        return attrs

    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        if instance.status != 'draft':
            raise serializers.ValidationError('Only draft exams can be edited.')
        return super().update(instance, validated_data)


class ExamResultSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student_enrollment.student.full_name', read_only=True)
    student_code = serializers.CharField(source='student_enrollment.student.student_code', read_only=True)
    exam_title = serializers.CharField(source='exam.title', read_only=True)
    subject_name = serializers.CharField(source='exam.teacher_assignment.subject.name', read_only=True)
    exam_date = serializers.DateField(source='exam.exam_date', read_only=True)
    exam_type_id = serializers.IntegerField(source='exam.exam_type_id', read_only=True)
    exam_type_name = serializers.CharField(source='exam.exam_type.name', read_only=True)
    exam_type_code = serializers.CharField(source='exam.exam_type.code', read_only=True)
    total_marks = serializers.DecimalField(
        source='exam.total_marks', max_digits=6, decimal_places=2, read_only=True,
    )
    academic_term_id = serializers.IntegerField(source='exam.academic_term_id', read_only=True)
    academic_term_name = serializers.CharField(source='exam.academic_term.name', read_only=True)
    percentage = serializers.SerializerMethodField()

    def get_percentage(self, obj):
        if obj.score is None or not obj.exam.total_marks:
            return None
        return round(obj.score * 100 / obj.exam.total_marks, 2)

    class Meta:
        model = ExamResult
        fields = (
            'id', 'exam', 'exam_title', 'student_enrollment', 'student_name',
            'student_code', 'subject_name', 'exam_date', 'exam_type_id',
            'exam_type_name', 'exam_type_code', 'total_marks', 'percentage',
            'academic_term_id', 'academic_term_name',
            'score', 'status', 'remarks',
            'workflow_status', 'approval_reason', 'graded_by', 'graded_at',
            'approved_by', 'approved_at', 'is_published', 'published_at',
            'published_by', 'created_at',
        )
        read_only_fields = (
            'id', 'workflow_status', 'approval_reason', 'graded_by', 'graded_at',
            'approved_by', 'approved_at', 'is_published', 'published_at',
            'published_by', 'created_at',
        )

    def validate(self, attrs):
        request = self.context.get('request')
        user = request.user if request else self.context['request'].user
        if request:
            from .context import require_writable_context
            require_writable_context(request)

        exam = attrs.get('exam', getattr(self.instance, 'exam', None))
        enrollment = attrs.get(
            'student_enrollment', getattr(self.instance, 'student_enrollment', None),
        )
        if not exams_for_user(user, request=request).filter(pk=exam.pk).exists():
            raise serializers.ValidationError('Exam is outside your scope.')
        if not get_accessible_student_enrollments_for_user(user, request=request).filter(pk=enrollment.pk).exists():
            raise serializers.ValidationError('Student enrollment is outside your scope.')
        assignment = exam.teacher_assignment
        if (
            enrollment.school_id != exam.school_id
            or enrollment.academic_year_id != exam.academic_year_id
            or enrollment.classroom_id != assignment.classroom_id
            or enrollment.section_id != assignment.section_id
        ):
            raise serializers.ValidationError('Invalid exam result relationships.')
        status_value = attrs.get('status', getattr(self.instance, 'status', 'not_graded'))
        score = attrs.get('score', getattr(self.instance, 'score', None))
        if status_value == 'present' and score is None:
            raise serializers.ValidationError({'score': 'Score is required.'})
        if status_value != 'present' and score is not None:
            raise serializers.ValidationError({'score': 'Score must be empty for this status.'})
        if score is not None and (score < 0 or score > exam.total_marks):
            raise serializers.ValidationError({'score': 'Score is outside the allowed range.'})
        return attrs

    def create(self, validated_data):
        request = self.context['request']
        return create_exam_result(changed_by=request.user, request=request, **validated_data)

    def update(self, instance, validated_data):
        request = self.context['request']
        validated_data.pop('exam', None)
        validated_data.pop('student_enrollment', None)
        return update_exam_result(
            exam_result=instance,
            changed_by=request.user,
            request=request,
            **validated_data,
        )


class PublicationSummarySerializer(serializers.Serializer):
    exam = serializers.IntegerField(source='exam.pk', read_only=True)
    published_count = serializers.IntegerField(read_only=True)
    skipped_count = serializers.IntegerField(read_only=True)
    already_published_count = serializers.IntegerField(read_only=True)
    unpublished_count = serializers.IntegerField(read_only=True, required=False)
    total_count = serializers.IntegerField(read_only=True)
    results = ExamResultSerializer(many=True, read_only=True)


class BulkGradeItemSerializer(serializers.Serializer):
    student_enrollment = serializers.PrimaryKeyRelatedField(
        queryset=StudentEnrollment.objects.all(),
    )
    score = serializers.DecimalField(max_digits=6, decimal_places=2, allow_null=True)
    status = serializers.ChoiceField(choices=ExamResult.STATUS_CHOICES)
    remarks = serializers.CharField(required=False, allow_blank=True, allow_null=True)


class BulkGradeSerializer(serializers.Serializer):
    exam = serializers.PrimaryKeyRelatedField(queryset=Exam.objects.all())
    results = BulkGradeItemSerializer(many=True, allow_empty=False)

    def validate(self, attrs):
        request = self.context['request']
        user = request.user
        from .context import require_writable_context
        require_writable_context(request)

        exam = attrs['exam']
        if not exams_for_user(user, request=request).filter(pk=exam.pk).exists():
            raise serializers.ValidationError({'exam': 'Exam is outside your scope.'})
        seen = set()
        assignment = exam.teacher_assignment
        for item in attrs['results']:
            enrollment = item['student_enrollment']
            if enrollment.pk in seen:
                raise serializers.ValidationError({'results': 'Duplicate students are not allowed.'})
            seen.add(enrollment.pk)
            if not get_accessible_student_enrollments_for_user(user, request=request).filter(pk=enrollment.pk).exists():
                raise serializers.ValidationError({'results': 'Student is outside your scope.'})
            if (
                enrollment.school_id != exam.school_id
                or enrollment.academic_year_id != exam.academic_year_id
                or enrollment.classroom_id != assignment.classroom_id
                or enrollment.section_id != assignment.section_id
            ):
                raise serializers.ValidationError({'results': 'Invalid exam relationships.'})
            score = item.get('score')
            if item['status'] == 'present' and score is None:
                raise serializers.ValidationError({'results': 'Present students require a score.'})
            if item['status'] != 'present' and score is not None:
                raise serializers.ValidationError({'results': 'Non-present students cannot have a score.'})
            if score is not None and (score < 0 or score > exam.total_marks):
                raise serializers.ValidationError({'results': 'Score is outside the allowed range.'})
        return attrs


    @transaction.atomic
    def create(self, validated_data):
        request = self.context['request']
        exam = validated_data['exam']
        saved = []
        for item in validated_data['results']:
            enrollment = item.pop('student_enrollment')
            existing = ExamResult.objects.filter(
                exam=exam, student_enrollment=enrollment,
            ).first()
            if existing:
                saved.append(update_exam_result(
                    exam_result=existing,
                    changed_by=request.user,
                    request=request,
                    **item,
                ))
            else:
                saved.append(create_exam_result(
                    exam=exam,
                    student_enrollment=enrollment,
                    changed_by=request.user,
                    request=request,
                    **item,
                ))
        return saved


class WorkflowActionSerializer(serializers.Serializer):
    reason = serializers.CharField(required=False, allow_blank=True, allow_null=True)


class BulkPublishSerializer(serializers.Serializer):
    exam_ids = serializers.ListField(
        child=serializers.IntegerField(min_value=1), allow_empty=False,
    )
    reason = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    def validate_exam_ids(self, value):
        if len(value) != len(set(value)):
            raise serializers.ValidationError('Duplicate exams are not allowed.')
        return value


class RejectActionSerializer(serializers.Serializer):
    reason = serializers.CharField(allow_blank=False)


class ExamResultLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExamResultLog
        fields = (
            'id', 'exam_result', 'old_score', 'new_score', 'old_status',
            'new_status', 'old_workflow_status', 'new_workflow_status',
            'old_approval_reason', 'new_approval_reason', 'old_is_published',
            'new_is_published', 'published_by', 'action', 'changed_by',
            'reason', 'request_id', 'ip_address', 'user_agent', 'changed_at',
        )
        read_only_fields = fields
