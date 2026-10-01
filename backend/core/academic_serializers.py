from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Count
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from .models import (
    AcademicTerm, AcademicYear, ClassSubject, Classroom, SchoolMembership, Section,
    Subject, Teacher, TeacherAssignment,
)
from .serializers import (
    AcademicYearBriefSerializer, ClassroomBriefSerializer,
    SchoolBriefSerializer, SectionBriefSerializer, SubjectBriefSerializer,
)
from .services.identity import sync_teacher_memberships

User = get_user_model()


class AcademicYearAdminSerializer(serializers.ModelSerializer):
    school = SchoolBriefSerializer(read_only=True)

    class Meta:
        model = AcademicYear
        fields = (
            'id', 'school', 'name', 'start_date', 'end_date', 'is_active',
            'created_at',
        )
        read_only_fields = ('id', 'school', 'created_at')

    def validate(self, attrs):
        school = getattr(self.context['request'], 'active_school', None)
        if not school:
            raise ValidationError('An active school context is required.')

        start_date = attrs.get('start_date', self.instance.start_date if self.instance else None)
        end_date = attrs.get('end_date', self.instance.end_date if self.instance else None)
        if start_date and end_date and start_date > end_date:
            raise ValidationError({'start_date': 'Start date must be on or before end date.'})

        if self.instance:
            boundary_errors = {}
            if self.instance.terms.filter(start_date__lt=start_date).exists():
                boundary_errors['start_date'] = 'Start date would exclude an existing academic term.'
            if self.instance.terms.filter(end_date__gt=end_date).exists():
                boundary_errors['end_date'] = 'End date would exclude an existing academic term.'
            if boundary_errors:
                raise ValidationError(boundary_errors)

        name = attrs.get('name', self.instance.name if self.instance else None)
        duplicate = AcademicYear.objects.filter(school=school, name=name)
        if self.instance:
            duplicate = duplicate.exclude(pk=self.instance.pk)
        if duplicate.exists():
            raise ValidationError({'name': 'An academic year with this name already exists.'})

        attrs['school'] = school
        return attrs


class AcademicTermAdminSerializer(serializers.ModelSerializer):
    school = SchoolBriefSerializer(read_only=True)
    academic_year = serializers.PrimaryKeyRelatedField(
        queryset=AcademicYear.objects.all(),
    )
    academic_year_detail = AcademicYearBriefSerializer(
        source='academic_year', read_only=True,
    )

    class Meta:
        model = AcademicTerm
        fields = (
            'id', 'school', 'academic_year', 'academic_year_detail', 'name',
            'term_type', 'start_date', 'end_date', 'is_active', 'created_at',
        )
        read_only_fields = ('id', 'school', 'academic_year_detail', 'created_at')

    def validate(self, attrs):
        school = getattr(self.context['request'], 'active_school', None)
        if not school:
            raise ValidationError('An active school context is required.')

        academic_year = attrs.get(
            'academic_year', self.instance.academic_year if self.instance else None,
        )
        if not academic_year or academic_year.school_id != school.id:
            raise ValidationError({
                'academic_year': 'Academic year must belong to the active school.',
            })

        start_date = attrs.get('start_date', self.instance.start_date if self.instance else None)
        end_date = attrs.get('end_date', self.instance.end_date if self.instance else None)
        if start_date and end_date and start_date > end_date:
            raise ValidationError({'start_date': 'Start date must be on or before end date.'})
        if start_date and start_date < academic_year.start_date:
            raise ValidationError({'start_date': 'Term must start within the academic year.'})
        if end_date and end_date > academic_year.end_date:
            raise ValidationError({'end_date': 'Term must end within the academic year.'})

        term_type = attrs.get('term_type', self.instance.term_type if self.instance else None)
        duplicate_type = AcademicTerm.objects.filter(
            school=school, academic_year=academic_year, term_type=term_type,
        )
        if self.instance:
            duplicate_type = duplicate_type.exclude(pk=self.instance.pk)
        if duplicate_type.exists():
            raise ValidationError({
                'term_type': 'This term type already exists for the academic year.',
            })

        if start_date and end_date:
            overlap = AcademicTerm.objects.filter(
                school=school,
                academic_year=academic_year,
                start_date__lte=end_date,
                end_date__gte=start_date,
            )
            if self.instance:
                overlap = overlap.exclude(pk=self.instance.pk)
            if overlap.exists():
                raise ValidationError({
                    'overlap': 'Term dates overlap an existing term; boundary dates are inclusive.',
                })

        attrs['school'] = school
        return attrs


class ClassroomAdminSerializer(serializers.ModelSerializer):
    school = SchoolBriefSerializer(read_only=True)
    academic_year = serializers.PrimaryKeyRelatedField(
        queryset=AcademicYear.objects.all(), required=False,
    )
    academic_year_detail = AcademicYearBriefSerializer(
        source='academic_year', read_only=True,
    )
    sections_count = serializers.SerializerMethodField(read_only=True)
    students_count = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Classroom
        fields = (
            'id', 'school', 'academic_year', 'academic_year_detail',
            'name', 'code', 'is_active', 'sections_count', 'students_count',
            'created_at',
        )
        read_only_fields = ('id', 'school', 'academic_year_detail', 'sections_count', 'students_count', 'created_at')

    @extend_schema_field(serializers.IntegerField())
    def get_sections_count(self, obj):
        return obj.sections.filter(is_active=True).count()

    @extend_schema_field(serializers.IntegerField())
    def get_students_count(self, obj):
        return obj.student_enrollments.filter(status='active', is_current=True).count()

    def validate(self, attrs):
        request = self.context['request']
        school = getattr(request, 'active_school', None) or getattr(request.user, 'school', None)
        if not school:
            raise ValidationError('An active school context is required.')

        if 'academic_year' not in attrs and not self.instance:
            year = getattr(request, 'active_academic_year', None)
            if not year:
                year = AcademicYear.objects.filter(school=school, is_active=True).order_by('-start_date', '-pk').first()
            if not year:
                raise ValidationError({'academic_year': 'Academic year is required.'})
            attrs['academic_year'] = year
        elif 'academic_year' in attrs:
            year = attrs['academic_year']
            if year.school_id != school.id:
                raise ValidationError({'academic_year': 'Academic year must belong to the active school.'})
        else:
            year = self.instance.academic_year

        code = attrs.get('code', self.instance.code if self.instance else None)
        qs = Classroom.objects.filter(school=school, academic_year=year, code=code)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError({'code': 'A classroom with this code already exists for the academic year.'})

        attrs['school'] = school
        return attrs


class SectionAdminSerializer(serializers.ModelSerializer):
    school = SchoolBriefSerializer(read_only=True)
    academic_year = serializers.PrimaryKeyRelatedField(read_only=True)
    academic_year_detail = AcademicYearBriefSerializer(
        source='academic_year', read_only=True,
    )
    classroom = serializers.PrimaryKeyRelatedField(
        queryset=Classroom.objects.all(),
    )
    classroom_detail = ClassroomBriefSerializer(
        source='classroom', read_only=True,
    )
    students_count = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Section
        fields = (
            'id', 'school', 'academic_year', 'academic_year_detail',
            'classroom', 'classroom_detail', 'name', 'code', 'is_active',
            'students_count', 'created_at',
        )
        read_only_fields = ('id', 'school', 'academic_year', 'academic_year_detail', 'classroom_detail', 'students_count', 'created_at')

    @extend_schema_field(serializers.IntegerField())
    def get_students_count(self, obj):
        return obj.student_enrollments.filter(status='active', is_current=True).count()

    def validate(self, attrs):
        request = self.context['request']
        school = getattr(request, 'active_school', None) or getattr(request.user, 'school', None)
        if not school:
            raise ValidationError('An active school context is required.')

        classroom = attrs.get('classroom', self.instance.classroom if self.instance else None)
        if not classroom or classroom.school_id != school.id:
            raise ValidationError({'classroom': 'Classroom must belong to the active school.'})

        year = classroom.academic_year
        code = attrs.get('code', self.instance.code if self.instance else None)
        qs = Section.objects.filter(school=school, academic_year=year, classroom=classroom, code=code)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError({'code': 'A section with this code already exists for the classroom.'})

        attrs['school'] = school
        attrs['academic_year'] = year
        return attrs


class SubjectAdminSerializer(serializers.ModelSerializer):
    school = SchoolBriefSerializer(read_only=True)

    class Meta:
        model = Subject
        fields = (
            'id', 'school', 'name', 'code', 'is_active',
        )
        read_only_fields = ('id', 'school')

    def validate(self, attrs):
        request = self.context['request']
        school = getattr(request, 'active_school', None) or getattr(request.user, 'school', None)
        if not school:
            raise ValidationError('An active school context is required.')

        code = attrs.get('code', self.instance.code if self.instance else None)
        qs = Subject.objects.filter(school=school, code=code)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError({'code': 'A subject with this code already exists in this school.'})

        attrs['school'] = school
        return attrs


class ClassSubjectAdminSerializer(serializers.ModelSerializer):
    school = SchoolBriefSerializer(read_only=True)
    academic_year = serializers.PrimaryKeyRelatedField(read_only=True)
    classroom = serializers.PrimaryKeyRelatedField(
        queryset=Classroom.objects.all(),
    )
    classroom_detail = ClassroomBriefSerializer(
        source='classroom', read_only=True,
    )
    subject = serializers.PrimaryKeyRelatedField(
        queryset=Subject.objects.all(),
    )
    subject_detail = SubjectBriefSerializer(
        source='subject', read_only=True,
    )

    class Meta:
        model = ClassSubject
        fields = (
            'id', 'school', 'academic_year', 'classroom', 'classroom_detail',
            'subject', 'subject_detail', 'weekly_periods',
        )
        read_only_fields = ('id', 'school', 'academic_year', 'classroom_detail', 'subject_detail')

    def validate(self, attrs):
        request = self.context['request']
        school = getattr(request, 'active_school', None) or getattr(request.user, 'school', None)
        if not school:
            raise ValidationError('An active school context is required.')

        classroom = attrs.get('classroom', self.instance.classroom if self.instance else None)
        subject = attrs.get('subject', self.instance.subject if self.instance else None)

        if not classroom or classroom.school_id != school.id:
            raise ValidationError({'classroom': 'Classroom must belong to the active school.'})
        if not subject or subject.school_id != school.id:
            raise ValidationError({'subject': 'Subject must belong to the active school.'})

        year = classroom.academic_year
        qs = ClassSubject.objects.filter(academic_year=year, classroom=classroom, subject=subject)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError('Subject is already assigned to this classroom in this academic year.')

        attrs['school'] = school
        attrs['academic_year'] = year
        return attrs


class TeacherAdminSerializer(serializers.ModelSerializer):
    school = SchoolBriefSerializer(read_only=True)
    academic_year = serializers.PrimaryKeyRelatedField(
        queryset=AcademicYear.objects.all(), required=False,
    )
    academic_year_detail = AcademicYearBriefSerializer(
        source='academic_year', read_only=True,
    )
    user = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), required=False, allow_null=True,
    )
    user_id = serializers.IntegerField(source='user.id', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    assignments_count = serializers.SerializerMethodField(read_only=True)

    # Optional write-only fields to create a login account alongside teacher profile
    account_username = serializers.CharField(
        write_only=True, required=False, allow_blank=True,
    )
    account_password = serializers.CharField(
        write_only=True, required=False, allow_blank=True,
    )

    class Meta:
        model = Teacher
        fields = (
            'id', 'school', 'academic_year', 'academic_year_detail',
            'user', 'user_id', 'username', 'employee_code', 'full_name',
            'phone', 'email', 'specialization', 'qualification', 'hire_date',
            'address', 'photo', 'is_active', 'assignments_count', 'created_at',
            'account_username', 'account_password',
        )
        read_only_fields = (
            'id', 'school', 'academic_year_detail', 'user_id', 'username',
            'employee_code', 'assignments_count', 'created_at',
        )

    @extend_schema_field(serializers.IntegerField())
    def get_assignments_count(self, obj):
        return obj.assignments.filter(is_current=True).count()

    def validate(self, attrs):
        request = self.context['request']
        school = getattr(request, 'active_school', None) or getattr(request.user, 'school', None)
        if not school:
            raise ValidationError('An active school context is required.')

        if 'academic_year' not in attrs and not self.instance:
            year = getattr(request, 'active_academic_year', None)
            if not year:
                year = AcademicYear.objects.filter(school=school, is_active=True).order_by('-start_date', '-pk').first()
            if not year:
                raise ValidationError({'academic_year': 'Academic year is required.'})
            attrs['academic_year'] = year
        elif 'academic_year' in attrs:
            year = attrs['academic_year']
            if year.school_id != school.id:
                raise ValidationError({'academic_year': 'Academic year must belong to the active school.'})

        user = attrs.get('user')
        if user:
            qs = Teacher.objects.filter(user=user)
            if self.instance:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise ValidationError({'user': 'A teacher profile is already linked to this user account.'})

        account_username = attrs.get('account_username')
        if account_username:
            if User.objects.filter(username=account_username).exists():
                raise ValidationError({'account_username': 'A user with this username already exists.'})

        attrs['school'] = school
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        account_username = validated_data.pop('account_username', None)
        account_password = validated_data.pop('account_password', None)
        school = validated_data['school']

        if account_username and account_password:
            full_name = validated_data.get('full_name', '')
            parts = full_name.strip().split(' ', 1)
            first_name = parts[0] if parts else ''
            last_name = parts[1] if len(parts) > 1 else ''
            email = validated_data.get('email', '')

            user = User.objects.create_user(
                username=account_username,
                password=account_password,
                first_name=first_name,
                last_name=last_name,
                email=email or '',
                role='teacher',
                school=school,
                is_active_school_user=True,
            )
            SchoolMembership.objects.create(
                user=user,
                school=school,
                role='teacher',
                status='active',
                is_default=True,
            )
            validated_data['user'] = user

        teacher = super().create(validated_data)
        if teacher.user_id:
            sync_teacher_memberships(teacher)
        return teacher

    @transaction.atomic
    def update(self, instance, validated_data):
        validated_data.pop('account_username', None)
        validated_data.pop('account_password', None)
        teacher = super().update(instance, validated_data)
        if teacher.user_id:
            sync_teacher_memberships(teacher)
        return teacher


class TeacherAssignmentAdminSerializer(serializers.ModelSerializer):
    school = SchoolBriefSerializer(read_only=True)
    academic_year = serializers.PrimaryKeyRelatedField(read_only=True)
    academic_year_detail = AcademicYearBriefSerializer(
        source='academic_year', read_only=True,
    )
    teacher = serializers.PrimaryKeyRelatedField(
        queryset=Teacher.objects.all(),
    )
    teacher_detail = serializers.SerializerMethodField(read_only=True)
    classroom = serializers.PrimaryKeyRelatedField(
        queryset=Classroom.objects.all(),
    )
    classroom_detail = ClassroomBriefSerializer(
        source='classroom', read_only=True,
    )
    section = serializers.PrimaryKeyRelatedField(
        queryset=Section.objects.all(),
    )
    section_detail = SectionBriefSerializer(
        source='section', read_only=True,
    )
    subject = serializers.PrimaryKeyRelatedField(
        queryset=Subject.objects.all(),
    )
    subject_detail = SubjectBriefSerializer(
        source='subject', read_only=True,
    )

    class Meta:
        model = TeacherAssignment
        fields = (
            'id', 'school', 'academic_year', 'academic_year_detail',
            'teacher', 'teacher_detail', 'classroom', 'classroom_detail',
            'section', 'section_detail', 'subject', 'subject_detail',
            'is_current', 'start_date', 'end_date', 'created_at',
        )
        read_only_fields = (
            'id', 'school', 'academic_year', 'academic_year_detail',
            'teacher_detail', 'classroom_detail', 'section_detail',
            'subject_detail', 'created_at',
        )

    @extend_schema_field(serializers.DictField())
    def get_teacher_detail(self, obj):
        teacher = obj.teacher
        return {
            'id': teacher.id,
            'full_name': teacher.full_name,
            'employee_code': teacher.employee_code,
            'specialization': teacher.specialization,
        }

    def validate(self, attrs):
        request = self.context['request']
        school = getattr(request, 'active_school', None) or getattr(request.user, 'school', None)
        if not school:
            raise ValidationError('An active school context is required.')

        teacher = attrs.get('teacher', self.instance.teacher if self.instance else None)
        classroom = attrs.get('classroom', self.instance.classroom if self.instance else None)
        section = attrs.get('section', self.instance.section if self.instance else None)
        subject = attrs.get('subject', self.instance.subject if self.instance else None)

        if not teacher or teacher.school_id != school.id:
            raise ValidationError({'teacher': 'Teacher must belong to the active school.'})
        if not classroom or classroom.school_id != school.id:
            raise ValidationError({'classroom': 'Classroom must belong to the active school.'})
        if not section or section.school_id != school.id:
            raise ValidationError({'section': 'Section must belong to the active school.'})
        if not subject or subject.school_id != school.id:
            raise ValidationError({'subject': 'Subject must belong to the active school.'})

        if section.classroom_id != classroom.id:
            raise ValidationError({'section': 'Section must belong to the selected classroom.'})
        if section.academic_year_id != classroom.academic_year_id:
            raise ValidationError({'section': 'Section academic year must match classroom academic year.'})

        year = classroom.academic_year
        qs = TeacherAssignment.objects.filter(
            teacher=teacher, academic_year=year, classroom=classroom,
            section=section, subject=subject,
        )
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError('This teacher assignment already exists for this section and subject.')

        # Ensure teacher has active membership in the school if linked to a user
        if teacher.user_id:
            memberships = SchoolMembership.objects.filter(
                user_id=teacher.user_id, school=school, role='teacher',
            )
            if not memberships.filter(status='active').exists():
                raise ValidationError({'teacher': 'Teacher requires an active membership in this school.'})

        attrs['school'] = school
        attrs['academic_year'] = year
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        assignment = super().create(validated_data)
        if assignment.teacher.user_id:
            sync_teacher_memberships(assignment.teacher)
        return assignment

    @transaction.atomic
    def update(self, instance, validated_data):
        assignment = super().update(instance, validated_data)
        if assignment.teacher.user_id:
            sync_teacher_memberships(assignment.teacher)
        return assignment
