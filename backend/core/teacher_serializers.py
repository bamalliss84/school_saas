from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from .models import (
    Attendance,
    Classroom,
    School,
    Section,
    Student,
    StudentEnrollment,
    Subject,
    Teacher,
    TeacherAssignment,
)
from .serializers import (
    AcademicYearBriefSerializer,
    ClassroomBriefSerializer,
    SchoolBriefSerializer,
    SectionBriefSerializer,
    SubjectBriefSerializer,
)


class TeacherProfileSerializer(serializers.ModelSerializer):
    school = SchoolBriefSerializer(read_only=True)
    academic_year = serializers.SerializerMethodField(read_only=True)
    role = serializers.SerializerMethodField(read_only=True)
    email = serializers.SerializerMethodField(read_only=True)
    phone = serializers.SerializerMethodField(read_only=True)
    user_id = serializers.IntegerField(source='user.id', read_only=True, allow_null=True)

    class Meta:
        model = Teacher
        fields = (
            'id',
            'user_id',
            'full_name',
            'email',
            'phone',
            'employee_code',
            'specialization',
            'qualification',
            'hire_date',
            'is_active',
            'school',
            'academic_year',
            'role',
            'created_at',
        )
        read_only_fields = fields

    @extend_schema_field(AcademicYearBriefSerializer)
    def get_academic_year(self, obj):
        request = self.context.get('request')
        year = getattr(request, 'active_academic_year', None) or obj.academic_year
        return AcademicYearBriefSerializer(year).data if year else None

    @extend_schema_field(serializers.CharField())
    def get_role(self, obj):
        request = self.context.get('request')
        return getattr(request, 'active_role', 'teacher')

    @extend_schema_field(serializers.CharField())
    def get_email(self, obj):
        if obj.email:
            return obj.email
        if obj.user and obj.user.email:
            return obj.user.email
        return ''

    @extend_schema_field(serializers.CharField())
    def get_phone(self, obj):
        if obj.phone:
            return obj.phone
        if obj.user and hasattr(obj.user, 'phone') and obj.user.phone:
            return obj.user.phone
        return ''


class RosterStudentBriefSerializer(serializers.ModelSerializer):
    photo_url = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Student
        fields = (
            'id',
            'student_code',
            'full_name',
            'gender',
            'photo_url',
        )
        read_only_fields = fields

    @extend_schema_field(serializers.CharField(allow_null=True))
    def get_photo_url(self, obj):
        if obj.photo:
            return obj.photo.url
        return None


class RosterAttendanceBriefSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attendance
        fields = (
            'id',
            'status',
            'note',
            'attendance_date',
            'academic_term',
        )
        read_only_fields = fields


class TeacherRosterItemSerializer(serializers.Serializer):
    student_enrollment_id = serializers.IntegerField()
    student = RosterStudentBriefSerializer()
    classroom = ClassroomBriefSerializer()
    section = SectionBriefSerializer()
    attendance = RosterAttendanceBriefSerializer(allow_null=True)


class TeacherAssignmentRosterResponseSerializer(serializers.Serializer):
    assignment_id = serializers.IntegerField()
    school = SchoolBriefSerializer()
    academic_year = AcademicYearBriefSerializer()
    classroom = ClassroomBriefSerializer()
    section = SectionBriefSerializer()
    subject = SubjectBriefSerializer()
    date = serializers.DateField()
    total_students = serializers.IntegerField()
    recorded_count = serializers.IntegerField()
    roster = TeacherRosterItemSerializer(many=True)
