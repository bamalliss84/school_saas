from django.db.models import Q
from drf_spectacular.utils import extend_schema
from rest_framework import generics, status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from .academic_serializers import (
    AcademicTermAdminSerializer, AcademicYearAdminSerializer,
    ClassSubjectAdminSerializer, ClassroomAdminSerializer,
    SectionAdminSerializer, SubjectAdminSerializer,
    TeacherAdminSerializer, TeacherAssignmentAdminSerializer,
)
from .context import require_writable_context
from .models import (
    AcademicTerm, AcademicYear, Attendance, ClassSubject, Classroom, Exam, Homework,
    Section, Subject, Teacher, TeacherAssignment, TimetableEntry,
)
from .pagination import StandardResultsSetPagination
from .permissions import IsActiveSchoolUser, IsSchoolAdminOrSuperAdmin


def _get_active_school(request):
    return getattr(request, 'active_school', None) or getattr(request.user, 'school', None)


def _get_active_academic_year(request):
    return getattr(request, 'active_academic_year', None) or getattr(request.user, 'academic_year', None)


class AcademicYearListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = AcademicYearAdminSerializer
    permission_classes = [IsActiveSchoolUser, IsSchoolAdminOrSuperAdmin]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return AcademicYear.objects.none()
        school = getattr(self.request, 'active_school', None)
        if not school:
            return AcademicYear.objects.none()
        queryset = AcademicYear.objects.filter(school=school).select_related('school')
        if 'is_active' in self.request.query_params:
            is_active = self.request.query_params['is_active'].lower() in ('true', '1')
            queryset = queryset.filter(is_active=is_active)
        return queryset.order_by('-start_date', '-pk')

    def perform_create(self, serializer):
        require_writable_context(self.request)
        serializer.save()


class AcademicYearDetailAPIView(generics.RetrieveUpdateAPIView):
    serializer_class = AcademicYearAdminSerializer
    permission_classes = [IsActiveSchoolUser, IsSchoolAdminOrSuperAdmin]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return AcademicYear.objects.none()
        school = getattr(self.request, 'active_school', None)
        if not school:
            return AcademicYear.objects.none()
        return AcademicYear.objects.filter(school=school).select_related('school')

    def perform_update(self, serializer):
        require_writable_context(self.request)
        serializer.save()


class AcademicTermListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = AcademicTermAdminSerializer
    permission_classes = [IsActiveSchoolUser, IsSchoolAdminOrSuperAdmin]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return AcademicTerm.objects.none()
        school = getattr(self.request, 'active_school', None)
        if not school:
            return AcademicTerm.objects.none()
        queryset = AcademicTerm.objects.filter(school=school).select_related(
            'school', 'academic_year',
        )
        year_id = self.request.query_params.get('academic_year_id')
        if year_id:
            queryset = queryset.filter(academic_year_id=year_id)
        if 'is_active' in self.request.query_params:
            is_active = self.request.query_params['is_active'].lower() in ('true', '1')
            queryset = queryset.filter(is_active=is_active)
        return queryset.order_by('academic_year__start_date', 'start_date', 'pk')

    def perform_create(self, serializer):
        require_writable_context(self.request)
        serializer.save()


class AcademicTermDetailAPIView(generics.RetrieveUpdateAPIView):
    serializer_class = AcademicTermAdminSerializer
    permission_classes = [IsActiveSchoolUser, IsSchoolAdminOrSuperAdmin]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return AcademicTerm.objects.none()
        school = getattr(self.request, 'active_school', None)
        if not school:
            return AcademicTerm.objects.none()
        return AcademicTerm.objects.filter(school=school).select_related(
            'school', 'academic_year',
        )

    def perform_update(self, serializer):
        require_writable_context(self.request)
        serializer.save()


class ClassroomListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = ClassroomAdminSerializer
    permission_classes = [IsActiveSchoolUser, IsSchoolAdminOrSuperAdmin]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Classroom.objects.none()
        school = _get_active_school(self.request)
        if not school:
            return Classroom.objects.none()

        qs = Classroom.objects.filter(school=school).select_related('school', 'academic_year')
        params = self.request.query_params

        year_id = params.get('academic_year_id')
        if year_id:
            qs = qs.filter(academic_year_id=year_id)
        else:
            year = _get_active_academic_year(self.request)
            if year and not params.get('all_years'):
                qs = qs.filter(academic_year=year)

        if 'is_active' in params:
            is_active_val = params['is_active'].lower() in ('true', '1')
            qs = qs.filter(is_active=is_active_val)

        search = params.get('search', '').strip()
        if search:
            qs = qs.filter(Q(name__icontains=search) | Q(code__icontains=search))

        return qs.order_by('name', 'code', 'id')

    def perform_create(self, serializer):
        require_writable_context(self.request)
        serializer.save()


class ClassroomDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ClassroomAdminSerializer
    permission_classes = [IsActiveSchoolUser, IsSchoolAdminOrSuperAdmin]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Classroom.objects.none()
        school = _get_active_school(self.request)
        if not school:
            return Classroom.objects.none()
        qs = Classroom.objects.filter(school=school).select_related('school', 'academic_year')
        year = _get_active_academic_year(self.request)
        if year:
            qs = qs.filter(academic_year=year)
        return qs

    def perform_update(self, serializer):
        require_writable_context(self.request)
        serializer.save()

    def perform_destroy(self, instance):
        require_writable_context(self.request)
        if instance.sections.exists():
            raise ValidationError('Cannot delete classroom with existing sections. Delete or move sections first.')
        if instance.student_enrollments.exists():
            raise ValidationError('Cannot delete classroom with existing student enrollments. Deactivate it instead.')
        if instance.teacher_assignments.exists():
            raise ValidationError('Cannot delete classroom with existing teacher assignments. Deactivate it instead.')
        if instance.class_subjects.exists():
            raise ValidationError('Cannot delete classroom with assigned subjects.')
        instance.delete()


class SectionListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = SectionAdminSerializer
    permission_classes = [IsActiveSchoolUser, IsSchoolAdminOrSuperAdmin]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Section.objects.none()
        school = _get_active_school(self.request)
        if not school:
            return Section.objects.none()

        qs = Section.objects.filter(school=school).select_related('school', 'academic_year', 'classroom')
        params = self.request.query_params

        classroom_id = params.get('classroom_id')
        if classroom_id:
            qs = qs.filter(classroom_id=classroom_id)

        year_id = params.get('academic_year_id')
        if year_id:
            qs = qs.filter(academic_year_id=year_id)
        else:
            year = _get_active_academic_year(self.request)
            if year and not params.get('all_years'):
                qs = qs.filter(academic_year=year)

        if 'is_active' in params:
            is_active_val = params['is_active'].lower() in ('true', '1')
            qs = qs.filter(is_active=is_active_val)

        search = params.get('search', '').strip()
        if search:
            qs = qs.filter(Q(name__icontains=search) | Q(code__icontains=search))

        return qs.order_by('classroom__name', 'name', 'code', 'id')

    def perform_create(self, serializer):
        require_writable_context(self.request)
        serializer.save()


class SectionDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = SectionAdminSerializer
    permission_classes = [IsActiveSchoolUser, IsSchoolAdminOrSuperAdmin]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Section.objects.none()
        school = _get_active_school(self.request)
        if not school:
            return Section.objects.none()
        qs = Section.objects.filter(school=school).select_related('school', 'academic_year', 'classroom')
        year = _get_active_academic_year(self.request)
        if year:
            qs = qs.filter(academic_year=year)
        return qs

    def perform_update(self, serializer):
        require_writable_context(self.request)
        serializer.save()

    def perform_destroy(self, instance):
        require_writable_context(self.request)
        if instance.student_enrollments.exists():
            raise ValidationError('Cannot delete section with existing student enrollments. Deactivate it instead.')
        if instance.teacher_assignments.exists():
            raise ValidationError('Cannot delete section with existing teacher assignments. Deactivate it instead.')
        instance.delete()


class SubjectListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = SubjectAdminSerializer
    permission_classes = [IsActiveSchoolUser, IsSchoolAdminOrSuperAdmin]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Subject.objects.none()
        school = _get_active_school(self.request)
        if not school:
            return Subject.objects.none()

        qs = Subject.objects.filter(school=school).select_related('school')
        params = self.request.query_params

        if 'is_active' in params:
            is_active_val = params['is_active'].lower() in ('true', '1')
            qs = qs.filter(is_active=is_active_val)

        search = params.get('search', '').strip()
        if search:
            qs = qs.filter(Q(name__icontains=search) | Q(code__icontains=search))

        return qs.order_by('name', 'code', 'id')

    def perform_create(self, serializer):
        require_writable_context(self.request)
        serializer.save()


class SubjectDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = SubjectAdminSerializer
    permission_classes = [IsActiveSchoolUser, IsSchoolAdminOrSuperAdmin]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Subject.objects.none()
        school = _get_active_school(self.request)
        if not school:
            return Subject.objects.none()
        return Subject.objects.filter(school=school).select_related('school')

    def perform_update(self, serializer):
        require_writable_context(self.request)
        serializer.save()

    def perform_destroy(self, instance):
        require_writable_context(self.request)
        if instance.class_subjects.exists():
            raise ValidationError('Cannot delete subject with allocated class curriculum. Remove class allocations first.')
        if instance.teacher_assignments.exists():
            raise ValidationError('Cannot delete subject with existing teacher assignments. Deactivate it instead.')
        instance.delete()


class ClassSubjectListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = ClassSubjectAdminSerializer
    permission_classes = [IsActiveSchoolUser, IsSchoolAdminOrSuperAdmin]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return ClassSubject.objects.none()
        school = _get_active_school(self.request)
        if not school:
            return ClassSubject.objects.none()

        qs = ClassSubject.objects.filter(school=school).select_related(
            'school', 'academic_year', 'classroom', 'subject',
        )
        params = self.request.query_params

        classroom_id = params.get('classroom_id')
        if classroom_id:
            qs = qs.filter(classroom_id=classroom_id)

        subject_id = params.get('subject_id')
        if subject_id:
            qs = qs.filter(subject_id=subject_id)

        year_id = params.get('academic_year_id')
        if year_id:
            qs = qs.filter(academic_year_id=year_id)
        else:
            year = _get_active_academic_year(self.request)
            if year and not params.get('all_years'):
                qs = qs.filter(academic_year=year)

        return qs.order_by('classroom__name', 'subject__name', 'id')

    def perform_create(self, serializer):
        require_writable_context(self.request)
        serializer.save()


class ClassSubjectDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ClassSubjectAdminSerializer
    permission_classes = [IsActiveSchoolUser, IsSchoolAdminOrSuperAdmin]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return ClassSubject.objects.none()
        school = _get_active_school(self.request)
        if not school:
            return ClassSubject.objects.none()
        qs = ClassSubject.objects.filter(school=school).select_related(
            'school', 'academic_year', 'classroom', 'subject',
        )
        year = _get_active_academic_year(self.request)
        if year:
            qs = qs.filter(academic_year=year)
        return qs

    def perform_update(self, serializer):
        require_writable_context(self.request)
        serializer.save()

    def perform_destroy(self, instance):
        require_writable_context(self.request)
        if TeacherAssignment.objects.filter(classroom=instance.classroom, subject=instance.subject).exists():
            raise ValidationError('Cannot delete class subject allocation with existing teacher assignments.')
        instance.delete()


class TeacherListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = TeacherAdminSerializer
    permission_classes = [IsActiveSchoolUser, IsSchoolAdminOrSuperAdmin]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Teacher.objects.none()
        school = _get_active_school(self.request)
        if not school:
            return Teacher.objects.none()

        qs = Teacher.objects.filter(school=school).select_related('school', 'academic_year', 'user')
        params = self.request.query_params

        year_id = params.get('academic_year_id')
        if year_id:
            qs = qs.filter(academic_year_id=year_id)
        else:
            year = _get_active_academic_year(self.request)
            if year and not params.get('all_years'):
                qs = qs.filter(academic_year=year)

        if 'is_active' in params:
            is_active_val = params['is_active'].lower() in ('true', '1')
            qs = qs.filter(is_active=is_active_val)

        search = params.get('search', '').strip()
        if search:
            qs = qs.filter(
                Q(full_name__icontains=search)
                | Q(employee_code__icontains=search)
                | Q(phone__icontains=search)
                | Q(email__icontains=search)
                | Q(specialization__icontains=search)
            )

        return qs.order_by('full_name', 'id')

    def perform_create(self, serializer):
        require_writable_context(self.request)
        serializer.save()


class TeacherDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = TeacherAdminSerializer
    permission_classes = [IsActiveSchoolUser, IsSchoolAdminOrSuperAdmin]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Teacher.objects.none()
        school = _get_active_school(self.request)
        if not school:
            return Teacher.objects.none()
        qs = Teacher.objects.filter(school=school).select_related('school', 'academic_year', 'user')
        year = _get_active_academic_year(self.request)
        if year:
            qs = qs.filter(academic_year=year)
        return qs

    def perform_update(self, serializer):
        require_writable_context(self.request)
        serializer.save()

    def perform_destroy(self, instance):
        require_writable_context(self.request)
        if instance.assignments.exists():
            raise ValidationError('Cannot delete teacher with existing assignments or operational records. Deactivate the teacher profile instead.')
        instance.delete()


class TeacherAssignmentListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = TeacherAssignmentAdminSerializer
    permission_classes = [IsActiveSchoolUser, IsSchoolAdminOrSuperAdmin]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return TeacherAssignment.objects.none()
        school = _get_active_school(self.request)
        if not school:
            return TeacherAssignment.objects.none()

        qs = TeacherAssignment.objects.filter(school=school).select_related(
            'school', 'academic_year', 'teacher', 'classroom', 'section', 'subject',
        )
        params = self.request.query_params

        teacher_id = params.get('teacher_id')
        if teacher_id:
            qs = qs.filter(teacher_id=teacher_id)

        classroom_id = params.get('classroom_id')
        if classroom_id:
            qs = qs.filter(classroom_id=classroom_id)

        section_id = params.get('section_id')
        if section_id:
            qs = qs.filter(section_id=section_id)

        subject_id = params.get('subject_id')
        if subject_id:
            qs = qs.filter(subject_id=subject_id)

        if 'is_current' in params:
            is_current_val = params['is_current'].lower() in ('true', '1')
            qs = qs.filter(is_current=is_current_val)

        year_id = params.get('academic_year_id')
        if year_id:
            qs = qs.filter(academic_year_id=year_id)
        else:
            year = _get_active_academic_year(self.request)
            if year and not params.get('all_years'):
                qs = qs.filter(academic_year=year)

        return qs.order_by('classroom__name', 'section__name', 'subject__name', 'teacher__full_name', 'id')

    def perform_create(self, serializer):
        require_writable_context(self.request)
        serializer.save()


class TeacherAssignmentDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = TeacherAssignmentAdminSerializer
    permission_classes = [IsActiveSchoolUser, IsSchoolAdminOrSuperAdmin]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return TeacherAssignment.objects.none()
        school = _get_active_school(self.request)
        if not school:
            return TeacherAssignment.objects.none()
        qs = TeacherAssignment.objects.filter(school=school).select_related(
            'school', 'academic_year', 'teacher', 'classroom', 'section', 'subject',
        )
        year = _get_active_academic_year(self.request)
        if year:
            qs = qs.filter(academic_year=year)
        return qs

    def perform_update(self, serializer):
        require_writable_context(self.request)
        serializer.save()

    def perform_destroy(self, instance):
        require_writable_context(self.request)
        has_timetable = TimetableEntry.objects.filter(teacher_assignment=instance).exists()
        has_attendance = Attendance.objects.filter(teacher_assignment=instance).exists()
        has_exams = Exam.objects.filter(teacher_assignment=instance).exists()
        has_homework = Homework.objects.filter(teacher_assignment=instance).exists()

        if has_timetable or has_attendance or has_exams or has_homework:
            raise ValidationError(
                'Cannot delete teacher assignment in use by timetable, attendance, exams, or homework. Mark is_current=False instead.'
            )
        instance.delete()
