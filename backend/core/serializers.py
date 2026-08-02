from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from drf_spectacular.utils import extend_schema_field, inline_serializer
from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.serializers import (
    TokenObtainPairSerializer,
    TokenRefreshSerializer,
)
from rest_framework_simplejwt.settings import api_settings
from rest_framework_simplejwt.tokens import RefreshToken

from .models import (
    AcademicTerm,
    AcademicYear,
    Attendance,
    Classroom,
    School,
    Section,
    Student,
    StudentEnrollment,
    StudentGuardian,
    Subject,
    TeacherAssignment,
    User,
)
from .selectors import (
    get_teacher_assignments_for_user,
    user_can_manage_teacher_assignment,
)


class SchoolBriefSerializer(serializers.ModelSerializer):
    class Meta:
        model = School
        fields = ('id', 'name')


class AcademicYearBriefSerializer(serializers.ModelSerializer):
    class Meta:
        model = AcademicYear
        fields = ('id', 'name')


class ClassroomBriefSerializer(serializers.ModelSerializer):
    class Meta:
        model = Classroom
        fields = ('id', 'name', 'code')


class SectionBriefSerializer(serializers.ModelSerializer):
    class Meta:
        model = Section
        fields = ('id', 'name', 'code')


class SubjectBriefSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = ('id', 'name', 'code')


class SchoolSerializer(serializers.ModelSerializer):
    class Meta:
        model = School
        fields = (
            'id', 'name', 'code', 'phone', 'email', 'address', 'is_active',
        )


class AcademicYearSerializer(serializers.ModelSerializer):
    school_name = serializers.CharField(source='school.name', read_only=True)

    class Meta:
        model = AcademicYear
        fields = (
            'id', 'school', 'school_name', 'name', 'start_date', 'end_date',
            'is_active',
        )


class UserSerializer(serializers.ModelSerializer):
    school_name = serializers.CharField(source='school.name', read_only=True)
    academic_year_name = serializers.CharField(
        source='academic_year.name',
        read_only=True,
    )

    class Meta:
        model = User
        fields = (
            'id', 'username', 'email', 'role', 'school', 'school_name',
            'academic_year', 'academic_year_name', 'phone', 'is_active',
        )


class UserContextSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    school = SchoolBriefSerializer(read_only=True)
    academic_year = AcademicYearBriefSerializer(read_only=True)
    linked_profile = serializers.SerializerMethodField()
    active_context = serializers.SerializerMethodField()
    contexts_count = serializers.SerializerMethodField()
    has_multiple_contexts = serializers.SerializerMethodField()
    legacy_role = serializers.CharField(source='_legacy_role', read_only=True, required=False)
    legacy_school = serializers.IntegerField(source='_legacy_school_id', read_only=True, required=False)

    class Meta:
        model = User
        fields = (
            'id', 'username', 'full_name', 'email', 'phone', 'role', 'school',
            'academic_year', 'linked_profile', 'active_context', 'contexts_count',
            'has_multiple_contexts', 'legacy_role', 'legacy_school',
        )

    def get_full_name(self, obj) -> str:
        return obj.get_full_name() or obj.username

    @extend_schema_field(
        inline_serializer(
            name='LinkedProfile',
            fields={
                'teacher_id': serializers.IntegerField(required=False),
                'parent_id': serializers.IntegerField(required=False),
                'student_id': serializers.IntegerField(required=False),
            },
        ),
    )
    def get_linked_profile(self, obj):
        relation_by_role = {
            'teacher': ('teacher_profile', 'teacher_id'),
            'parent': ('parent_profile', 'parent_id'),
            'student': ('student_profile', 'student_id'),
        }
        relation = relation_by_role.get(obj.role)
        if relation is None:
            return None
        relation_name, key = relation
        try:
            profile = getattr(obj, relation_name)
        except ObjectDoesNotExist:
            return None
        return {key: profile.pk}



    def _memberships(self, obj):
        from .context import get_user_memberships
        return get_user_memberships(obj)

    def get_active_context(self, obj) -> dict | None:
        from .context_serializers import SchoolMembershipSerializer
        request = self.context.get('request')
        membership = getattr(request, 'active_membership', None) if request else None
        if membership is None:
            membership = self._memberships(obj).filter(is_default=True, status='active').first()
            membership = membership or self._memberships(obj).filter(status='active').first()
        return SchoolMembershipSerializer(
            membership, context={'request': request},
        ).data if membership else None

    def get_contexts_count(self, obj) -> int:
        return self._memberships(obj).count()

    def get_has_multiple_contexts(self, obj) -> bool:
        return self.get_contexts_count(obj) > 1

class LoginTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        from .context import ensure_legacy_membership, get_user_memberships
        if not self.user.is_active_school_user:
            raise AuthenticationFailed('Authentication failed.')
        ensure_legacy_membership(self.user)
        usable = get_user_memberships(self.user).filter(
            status__in=('active', 'historical'), school__is_active=True,
        )
        if self.user.role != 'super_admin' and not usable.exists():
            raise AuthenticationFailed('Authentication failed.')
        default = usable.filter(status='active', is_default=True).first()
        data['user'] = UserContextSerializer(
            self.user, context=self.context,
        ).data
        data['contexts_count'] = usable.count()
        data['has_multiple_contexts'] = usable.count() > 1
        data['default_membership_id'] = default.pk if default else None
        return data


class SecureTokenRefreshSerializer(TokenRefreshSerializer):
    def validate(self, attrs):
        try:
            token = RefreshToken(attrs['refresh'])
        except TokenError:
            return super().validate(attrs)

        user_id = token.get(api_settings.USER_ID_CLAIM)
        user = None
        if user_id is not None:
            user = get_user_model().objects.select_related('school').filter(
                **{api_settings.USER_ID_FIELD: user_id}
            ).first()

        if user is None or not user.is_active or not user.is_active_school_user:
            raise AuthenticationFailed('Authentication failed.')
        from .context import ensure_legacy_membership, get_user_memberships
        ensure_legacy_membership(user)
        usable = get_user_memberships(user).filter(
            status__in=('active', 'historical'), school__is_active=True,
        )
        if user.role != 'super_admin' and not usable.exists():
            raise AuthenticationFailed('Authentication failed.')
        return super().validate(attrs)


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()

    def validate_refresh(self, value):
        try:
            token = RefreshToken(value)
        except TokenError as exc:
            raise serializers.ValidationError('Invalid refresh token.') from exc

        request = self.context.get('request')
        token_user_id = token.get(api_settings.USER_ID_CLAIM)
        if (
            request is None
            or not request.user.is_authenticated
            or token_user_id is None
            or str(token_user_id) != str(request.user.pk)
        ):
            raise serializers.ValidationError('Invalid refresh token.')

        self.token = token
        return value

    def save(self, **kwargs):
        self.token.blacklist()


class StudentEnrollmentSerializer(serializers.ModelSerializer):
    school = SchoolBriefSerializer(read_only=True)
    academic_year = AcademicYearBriefSerializer(read_only=True)
    classroom = ClassroomBriefSerializer(read_only=True)
    section = SectionBriefSerializer(read_only=True)

    class Meta:
        model = StudentEnrollment
        fields = (
            'id', 'school', 'academic_year', 'classroom', 'section', 'status',
            'is_current', 'start_date', 'end_date', 'created_at',
        )


class GuardianSerializer(serializers.ModelSerializer):
    parent_id = serializers.IntegerField(source='parent.id', read_only=True)
    full_name = serializers.CharField(source='parent.full_name', read_only=True)

    class Meta:
        model = StudentGuardian
        fields = ('parent_id', 'full_name', 'relationship', 'is_primary')


class StudentListSerializer(serializers.ModelSerializer):
    school = SchoolBriefSerializer(read_only=True)
    current_enrollment = serializers.SerializerMethodField()

    class Meta:
        model = Student
        fields = (
            'id', 'student_code', 'full_name', 'gender', 'birth_date',
            'is_active', 'created_at', 'school', 'current_enrollment',
        )

    @extend_schema_field(StudentEnrollmentSerializer(allow_null=True))
    def get_current_enrollment(self, obj):
        enrollment = next(
            (
                item for item in obj.enrollments.all()
                if item.is_current and item.status == 'active'
            ),
            None,
        )
        return StudentEnrollmentSerializer(enrollment).data if enrollment else None


class StudentDetailSerializer(StudentListSerializer):
    guardians = serializers.SerializerMethodField()

    class Meta(StudentListSerializer.Meta):
        fields = StudentListSerializer.Meta.fields + ('guardians',)

    @extend_schema_field(GuardianSerializer(many=True))
    def get_guardians(self, obj):
        request = self.context.get('request')
        if request is None or request.user.role == 'student':
            return []
        return GuardianSerializer(obj.guardians.all(), many=True).data


class ParentChildSerializer(serializers.ModelSerializer):
    student = StudentListSerializer(read_only=True)
    relationship_type = serializers.CharField(
        source='relationship',
        read_only=True,
    )

    class Meta:
        model = StudentGuardian
        fields = ('student', 'relationship_type', 'is_primary')


class TeacherAssignmentSerializer(serializers.ModelSerializer):
    school = SchoolBriefSerializer(read_only=True)
    academic_year = AcademicYearBriefSerializer(read_only=True)
    classroom = ClassroomBriefSerializer(read_only=True)
    section = SectionBriefSerializer(read_only=True)
    subject = SubjectBriefSerializer(read_only=True)

    class Meta:
        model = TeacherAssignment
        fields = (
            'id', 'school', 'academic_year', 'classroom', 'section', 'subject',
            'start_date', 'end_date', 'is_current',
        )


class TeacherClassSerializer(serializers.ModelSerializer):
    classroom = ClassroomBriefSerializer(read_only=True)
    section = SectionBriefSerializer(read_only=True)

    class Meta:
        model = TeacherAssignment
        fields = ('classroom', 'section')

class AcademicTermBriefSerializer(serializers.ModelSerializer):
    class Meta:
        model = AcademicTerm
        fields = ('id', 'name', 'term_type', 'start_date', 'end_date')


def _validate_teacher_assignment_for_write(user, assignment, attendance_date):
    if user.role != 'teacher':
        return
    if (
        not user_can_manage_teacher_assignment(user, assignment)
        or not assignment.is_current
        or (
            user.academic_year_id
            and assignment.academic_year_id != user.academic_year_id
        )
        or (assignment.start_date and attendance_date < assignment.start_date)
        or (assignment.end_date and attendance_date > assignment.end_date)
    ):
        raise serializers.ValidationError('Invalid attendance relationships.')


class AttendanceSerializer(serializers.ModelSerializer):
    student = serializers.SerializerMethodField(read_only=True)
    academic_term_detail = AcademicTermBriefSerializer(
        source='academic_term', read_only=True,
    )

    class Meta:
        model = Attendance
        fields = (
            'id', 'student_enrollment', 'student', 'teacher_assignment',
            'academic_term', 'academic_term_detail', 'attendance_date',
            'status', 'note', 'created_at',
        )
        read_only_fields = ('id', 'student', 'academic_term_detail', 'created_at')

    @extend_schema_field(
        inline_serializer(
            name='AttendanceStudent',
            fields={
                'id': serializers.IntegerField(),
                'student_code': serializers.CharField(),
                'full_name': serializers.CharField(),
            },
        ),
    )
    def get_student(self, obj):
        student = obj.student_enrollment.student
        return {
            'id': student.id,
            'student_code': student.student_code,
            'full_name': student.full_name,
        }

    def validate(self, attrs):
        request = self.context['request']
        user = request.user
        instance = self.instance
        enrollment = attrs.get(
            'student_enrollment',
            instance.student_enrollment if instance else None,
        )
        assignment = attrs.get(
            'teacher_assignment',
            instance.teacher_assignment if instance else None,
        )
        term = attrs.get('academic_term', instance.academic_term if instance else None)
        attendance_date = attrs.get(
            'attendance_date', instance.attendance_date if instance else None,
        )

        if user.role not in ('super_admin', 'school_admin', 'teacher'):
            raise serializers.ValidationError('Attendance cannot be managed by this role.')
        if enrollment is None or term is None:
            return attrs
        enrollment_changed = (
            instance is None
            or (
                'student_enrollment' in attrs
                and attrs['student_enrollment'].pk != instance.student_enrollment_id
            )
        )
        if enrollment_changed and (
            enrollment.status != 'active' or not enrollment.is_current
        ):
            raise serializers.ValidationError('Student enrollment must be active and current.')
        if user.role != 'super_admin' and enrollment.school_id != user.school_id:
            raise serializers.ValidationError('Invalid attendance relationships.')
        if term.school_id != enrollment.school_id or term.academic_year_id != enrollment.academic_year_id:
            raise serializers.ValidationError('Invalid attendance relationships.')
        if attendance_date and not (term.start_date <= attendance_date <= term.end_date):
            raise serializers.ValidationError('Attendance date must be inside the academic term.')
        if assignment:
            if (
                assignment.school_id != enrollment.school_id
                or assignment.academic_year_id != enrollment.academic_year_id
                or assignment.classroom_id != enrollment.classroom_id
                or assignment.section_id != enrollment.section_id
            ):
                raise serializers.ValidationError('Invalid attendance relationships.')
            if not user_can_manage_teacher_assignment(user, assignment):
                raise serializers.ValidationError('Invalid attendance relationships.')
            _validate_teacher_assignment_for_write(
                user, assignment, attendance_date,
            )
        elif user.role == 'teacher':
            raise serializers.ValidationError('Teacher assignment is required.')

        if enrollment and attendance_date:
            duplicate = Attendance.objects.filter(
                student_enrollment=enrollment,
                attendance_date=attendance_date,
            )
            if instance:
                duplicate = duplicate.exclude(pk=instance.pk)
            if duplicate.exists():
                raise serializers.ValidationError('Attendance already exists for this student and date.')
        return attrs


class BulkAttendanceStudentSerializer(serializers.Serializer):
    student_enrollment_id = serializers.IntegerField(min_value=1)
    status = serializers.ChoiceField(choices=Attendance.STATUS_CHOICES)
    note = serializers.CharField(required=False, allow_blank=True, allow_null=True)


class BulkAttendanceSerializer(serializers.Serializer):
    teacher_assignment_id = serializers.IntegerField(min_value=1)
    attendance_date = serializers.DateField()
    academic_term_id = serializers.IntegerField(min_value=1)
    students = BulkAttendanceStudentSerializer(many=True, allow_empty=False)

    def validate(self, attrs):
        user = self.context['request'].user
        assignment = get_teacher_assignments_for_user(user).filter(
            pk=attrs['teacher_assignment_id'],
        ).first()
        if assignment is None or user.role not in ('super_admin', 'school_admin', 'teacher'):
            raise serializers.ValidationError('Invalid attendance scope.')

        term = AcademicTerm.objects.filter(
            pk=attrs['academic_term_id'],
            school_id=assignment.school_id,
            academic_year_id=assignment.academic_year_id,
        ).first()
        if term is None:
            raise serializers.ValidationError('Invalid attendance scope.')
        _validate_teacher_assignment_for_write(
            user, assignment, attrs['attendance_date'],
        )
        if not (term.start_date <= attrs['attendance_date'] <= term.end_date):
            raise serializers.ValidationError('Attendance date must be inside the academic term.')

        enrollment_ids = [item['student_enrollment_id'] for item in attrs['students']]
        if len(enrollment_ids) != len(set(enrollment_ids)):
            raise serializers.ValidationError({'students': 'Duplicate student enrollment IDs are not allowed.'})

        enrollments = {
            item.id: item
            for item in StudentEnrollment.objects.select_related('student').filter(
                id__in=enrollment_ids,
            )
        }
        if len(enrollments) != len(enrollment_ids):
            raise serializers.ValidationError('Invalid attendance scope.')
        resolved_students = []
        for item in attrs['students']:
            enrollment = enrollments[item['student_enrollment_id']]
            if (
                enrollment.school_id != assignment.school_id
                or enrollment.academic_year_id != assignment.academic_year_id
                or enrollment.classroom_id != assignment.classroom_id
                or enrollment.section_id != assignment.section_id
                or enrollment.status != 'active'
                or not enrollment.is_current
            ):
                raise serializers.ValidationError('Invalid attendance scope.')
            resolved_students.append({**item, 'student_enrollment': enrollment})

        attrs['teacher_assignment'] = assignment
        attrs['academic_term'] = term
        attrs['students'] = resolved_students
        return attrs
