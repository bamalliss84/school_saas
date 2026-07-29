from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
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
    AcademicYear,
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

    class Meta:
        model = User
        fields = (
            'id', 'username', 'full_name', 'email', 'phone', 'role', 'school',
            'academic_year', 'linked_profile',
        )

    def get_full_name(self, obj):
        return obj.get_full_name() or obj.username

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


class LoginTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        if not self.user.is_active_school_user:
            raise AuthenticationFailed('Authentication failed.')
        if self.user.school_id and not self.user.school.is_active:
            raise AuthenticationFailed('Authentication failed.')
        data['user'] = UserContextSerializer(self.user).data
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

        if (
            user is None
            or not user.is_active
            or not user.is_active_school_user
            or (
                user.role != 'super_admin'
                and (user.school_id is None or not user.school.is_active)
            )
        ):
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