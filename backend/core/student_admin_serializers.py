from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from .models import AcademicYear, Classroom, Section, Student, StudentEnrollment
from .serializers import AcademicYearBriefSerializer, ClassroomBriefSerializer, SchoolBriefSerializer, SectionBriefSerializer
from .services.identity import create_student_enrollment, update_student_enrollment


class StudentAdminWriteSerializer(serializers.ModelSerializer):
    school = SchoolBriefSerializer(read_only=True)

    class Meta:
        model = Student
        fields = (
            'id', 'student_code', 'school', 'full_name', 'gender', 'birth_date',
            'photo', 'is_active', 'created_at',
        )
        read_only_fields = ('id', 'student_code', 'school', 'created_at')

    def create(self, validated_data):
        school = getattr(self.context['request'], 'active_school', None)
        if not school:
            raise ValidationError('An active school context is required.')
        return Student.objects.create(school=school, **validated_data)


class StudentEnrollmentAdminSerializer(serializers.ModelSerializer):
    academic_year = serializers.PrimaryKeyRelatedField(queryset=AcademicYear.objects.all())
    classroom = serializers.PrimaryKeyRelatedField(queryset=Classroom.objects.all())
    section = serializers.PrimaryKeyRelatedField(queryset=Section.objects.all())
    academic_year_detail = AcademicYearBriefSerializer(source='academic_year', read_only=True)
    classroom_detail = ClassroomBriefSerializer(source='classroom', read_only=True)
    section_detail = SectionBriefSerializer(source='section', read_only=True)

    class Meta:
        model = StudentEnrollment
        fields = (
            'id', 'academic_year', 'academic_year_detail', 'classroom',
            'classroom_detail', 'section', 'section_detail', 'status',
            'is_current', 'start_date', 'end_date', 'created_at',
        )
        read_only_fields = ('id', 'academic_year_detail', 'classroom_detail', 'section_detail', 'created_at')

    def validate(self, attrs):
        request = self.context['request']
        school = getattr(request, 'active_school', None)
        student = self.context.get('student') or (self.instance.student if self.instance else None)
        if not school or not student:
            raise ValidationError('Active school and student context are required.')

        year = attrs.get('academic_year', self.instance.academic_year if self.instance else None)
        classroom = attrs.get('classroom', self.instance.classroom if self.instance else None)
        section = attrs.get('section', self.instance.section if self.instance else None)
        status = attrs.get('status', self.instance.status if self.instance else 'active')
        is_current = attrs.get('is_current', self.instance.is_current if self.instance else False)
        start_date = attrs.get('start_date', self.instance.start_date if self.instance else None)
        end_date = attrs.get('end_date', self.instance.end_date if self.instance else None)

        errors = {}
        if not year or year.school_id != school.pk:
            errors['academic_year'] = 'Academic year must belong to the active school.'
        if not classroom or classroom.school_id != school.pk or (year and classroom.academic_year_id != year.pk):
            errors['classroom'] = 'Classroom must belong to the selected school and academic year.'
        if (
            not section or section.school_id != school.pk
            or (year and section.academic_year_id != year.pk)
            or (classroom and section.classroom_id != classroom.pk)
        ):
            errors['section'] = 'Section must belong to the selected classroom and academic year.'
        if is_current and status != 'active':
            errors['is_current'] = 'A current enrollment must be active.'
        if start_date and end_date and start_date > end_date:
            errors['end_date'] = 'End date must be on or after start date.'
        if year and start_date and start_date < year.start_date:
            errors['start_date'] = 'Start date must fall within the academic year.'
        if year and end_date and end_date > year.end_date:
            errors['end_date'] = 'End date must fall within the academic year.'
        duplicate = StudentEnrollment.objects.filter(student=student, academic_year=year)
        if self.instance:
            duplicate = duplicate.exclude(pk=self.instance.pk)
        if year and duplicate.exists():
            errors['academic_year'] = 'This student already has an enrollment for the academic year.'
        if errors:
            raise ValidationError(errors)
        return attrs

    def create(self, validated_data):
        return create_student_enrollment(
            student=self.context['student'], school=self.context['request'].active_school,
            **validated_data,
        )

    def update(self, instance, validated_data):
        return update_student_enrollment(
            enrollment=instance, school=self.context['request'].active_school,
            **validated_data,
        )
