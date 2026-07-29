from rest_framework import serializers

from .models import Attendance


class DateRangeQuerySerializer(serializers.Serializer):
    date_from = serializers.DateField(required=False)
    date_to = serializers.DateField(required=False)

    def validate(self, attrs):
        if (
            attrs.get('date_from')
            and attrs.get('date_to')
            and attrs['date_from'] > attrs['date_to']
        ):
            raise serializers.ValidationError(
                {'date_to': 'date_to must be on or after date_from.'},
            )
        return attrs


class StudentListQuerySerializer(serializers.Serializer):
    search = serializers.CharField(required=False, allow_blank=True)
    is_active = serializers.BooleanField(required=False)
    school_id = serializers.IntegerField(required=False, min_value=1)
    academic_year_id = serializers.IntegerField(required=False, min_value=1)
    classroom_id = serializers.IntegerField(required=False, min_value=1)
    section_id = serializers.IntegerField(required=False, min_value=1)
    enrollment_status = serializers.ChoiceField(
        required=False,
        choices=(
            'active', 'transferred', 'graduated', 'withdrawn', 'suspended',
        ),
    )
    is_current = serializers.BooleanField(required=False)
    ordering = serializers.ChoiceField(
        required=False,
        default='full_name',
        choices=(
            'full_name', '-full_name', 'student_code', '-student_code',
            'created_at', '-created_at',
        ),
    )


class TeacherAssignmentQuerySerializer(serializers.Serializer):
    current = serializers.BooleanField(required=False)
    academic_year_id = serializers.IntegerField(required=False, min_value=1)
    classroom_id = serializers.IntegerField(required=False, min_value=1)
    section_id = serializers.IntegerField(required=False, min_value=1)
    subject_id = serializers.IntegerField(required=False, min_value=1)
    date = serializers.DateField(required=False)
    ordering = serializers.ChoiceField(
        required=False,
        default='-is_current',
        choices=(
            'created_at', '-created_at', 'start_date', '-start_date',
            'classroom__name', '-classroom__name', 'is_current', '-is_current',
        ),
    )


class AttendanceListQuerySerializer(DateRangeQuerySerializer):
    attendance_date = serializers.DateField(required=False)
    status = serializers.ChoiceField(
        required=False,
        choices=Attendance.STATUS_CHOICES,
    )
    student_id = serializers.IntegerField(required=False, min_value=1)
    student_enrollment_id = serializers.IntegerField(required=False, min_value=1)
    teacher_assignment_id = serializers.IntegerField(required=False, min_value=1)
    academic_year_id = serializers.IntegerField(required=False, min_value=1)
    academic_term_id = serializers.IntegerField(required=False, min_value=1)
    classroom_id = serializers.IntegerField(required=False, min_value=1)
    section_id = serializers.IntegerField(required=False, min_value=1)
    search = serializers.CharField(required=False, allow_blank=True)
    ordering = serializers.ChoiceField(
        required=False,
        default='-attendance_date',
        choices=(
            'attendance_date', '-attendance_date',
            'student_enrollment__student__full_name',
            '-student_enrollment__student__full_name',
            'status', '-status', 'created_at', '-created_at',
        ),
    )


class DailyAttendanceReportQuerySerializer(serializers.Serializer):
    date = serializers.DateField(required=False)
    teacher_assignment_id = serializers.IntegerField(required=False, min_value=1)
    classroom_id = serializers.IntegerField(required=False, min_value=1)
    section_id = serializers.IntegerField(required=False, min_value=1)
    status = serializers.ChoiceField(
        required=False,
        choices=Attendance.STATUS_CHOICES,
    )


class StudentAttendanceSummaryQuerySerializer(DateRangeQuerySerializer):
    academic_year_id = serializers.IntegerField(required=False, min_value=1)
    academic_term_id = serializers.IntegerField(required=False, min_value=1)


class ClassAttendanceSummaryQuerySerializer(
    StudentAttendanceSummaryQuerySerializer,
):
    section_id = serializers.IntegerField(required=False, min_value=1)
    teacher_assignment_id = serializers.IntegerField(required=False, min_value=1)
