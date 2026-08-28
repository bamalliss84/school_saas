from datetime import datetime
from django.db.models import Min, Q, Subquery
from django.utils import timezone
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework import generics, status
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

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
from .permissions import IsActiveSchoolUser, IsTeacher
from .query_serializers import TeacherAssignmentQuerySerializer
from .serializers import (
    StudentListSerializer,
    SubjectBriefSerializer,
    TeacherAssignmentSerializer,
    TeacherClassSerializer,
)
from .teacher_serializers import (
    TeacherAssignmentRosterResponseSerializer,
    TeacherProfileSerializer,
)


def _get_active_school(request):
    return getattr(request, 'active_school', None) or getattr(request.user, 'school', None)


def _get_active_academic_year(request):
    return getattr(request, 'active_academic_year', None) or getattr(request.user, 'academic_year', None)


def _get_teacher_for_request(request):
    school = _get_active_school(request)
    teacher = Teacher.objects.filter(user=request.user, school=school).first()
    if not teacher:
        teacher = Teacher.objects.filter(user=request.user).first()
    if not teacher or (school and teacher.school_id != school.id):
        raise NotFound('Teacher profile not found.')
    return teacher


def _current_assignments_for_request(request):
    school = _get_active_school(request)
    active_year = _get_active_academic_year(request)
    queryset = TeacherAssignment.objects.filter(
        teacher__user=request.user,
        school=school,
        is_current=True,
    )
    if active_year:
        queryset = queryset.filter(academic_year=active_year)
    else:
        queryset = queryset.filter(academic_year__is_active=True)
    return queryset


class TeacherMeProfileAPIView(generics.RetrieveAPIView):
    serializer_class = TeacherProfileSerializer
    permission_classes = [IsActiveSchoolUser, IsTeacher]

    @extend_schema(responses={200: TeacherProfileSerializer})
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_object(self):
        return _get_teacher_for_request(self.request)


class TeacherAssignmentsAPIView(generics.ListAPIView):
    serializer_class = TeacherAssignmentSerializer
    permission_classes = [IsActiveSchoolUser, IsTeacher]

    @extend_schema(parameters=[TeacherAssignmentQuerySerializer])
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return TeacherAssignment.objects.none()

        query = TeacherAssignmentQuerySerializer(data=self.request.query_params)
        query.is_valid(raise_exception=True)
        params = query.validated_data

        school = _get_active_school(self.request)
        active_year = _get_active_academic_year(self.request)

        queryset = TeacherAssignment.objects.filter(
            teacher__user=self.request.user,
            school=school,
        )

        if params.get('current'):
            queryset = _current_assignments_for_request(self.request)
        elif params.get('academic_year_id'):
            queryset = queryset.filter(academic_year_id=params['academic_year_id'])
        elif active_year:
            queryset = queryset.filter(academic_year=active_year)

        field_filters = {
            'classroom_id': 'classroom_id',
            'section_id': 'section_id',
            'subject_id': 'subject_id',
        }
        for parameter, field in field_filters.items():
            if parameter in params:
                queryset = queryset.filter(**{field: params[parameter]})

        if params.get('date'):
            selected_date = params['date']
            queryset = queryset.filter(
                Q(start_date__isnull=True) | Q(start_date__lte=selected_date),
                Q(end_date__isnull=True) | Q(end_date__gte=selected_date),
            )

        return queryset.select_related(
            'school', 'academic_year', 'classroom', 'section', 'subject',
        ).order_by(params.get('ordering', 'classroom__name'), 'id')


class TeacherClassesAPIView(generics.ListAPIView):
    serializer_class = TeacherClassSerializer
    permission_classes = [IsActiveSchoolUser, IsTeacher]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return TeacherAssignment.objects.none()

        assignments = _current_assignments_for_request(self.request)
        unique_ids = assignments.values('classroom_id', 'section_id').annotate(
            first_id=Min('id'),
        ).values('first_id')

        return TeacherAssignment.objects.filter(
            pk__in=Subquery(unique_ids),
        ).select_related('classroom', 'section').order_by(
            'classroom__name', 'section__name',
        )


class TeacherSubjectsAPIView(generics.ListAPIView):
    serializer_class = SubjectBriefSerializer
    permission_classes = [IsActiveSchoolUser, IsTeacher]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Subject.objects.none()

        school = _get_active_school(self.request)
        assignments = _current_assignments_for_request(self.request)
        return Subject.objects.filter(
            teacher_assignments__in=assignments,
            school=school,
        ).distinct().order_by('name')


class TeacherStudentsAPIView(generics.ListAPIView):
    serializer_class = StudentListSerializer
    permission_classes = [IsActiveSchoolUser, IsTeacher]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Student.objects.none()

        school = _get_active_school(self.request)
        active_year = _get_active_academic_year(self.request)
        assignments = _current_assignments_for_request(self.request)

        pairs = list(assignments.values_list('classroom_id', 'section_id').distinct())
        if not pairs:
            return Student.objects.none()

        scope = Q()
        for classroom_id, section_id in pairs:
            scope |= Q(classroom_id=classroom_id, section_id=section_id)

        enrollments = StudentEnrollment.objects.filter(
            school=school,
            status='active',
            is_current=True,
        )
        if active_year:
            enrollments = enrollments.filter(academic_year=active_year)
        enrollments = enrollments.filter(scope)

        student_ids = enrollments.values_list('student_id', flat=True).distinct()
        return Student.objects.filter(id__in=student_ids).order_by('full_name')


class TeacherAssignmentStudentsAPIView(APIView):
    permission_classes = [IsActiveSchoolUser, IsTeacher]

    @extend_schema(
        responses={200: TeacherAssignmentRosterResponseSerializer},
    )
    def get(self, request, assignment_id):
        school = _get_active_school(request)
        active_year = _get_active_academic_year(request)

        assignment = generics.get_object_or_404(
            TeacherAssignment.objects.select_related(
                'school', 'academic_year', 'classroom', 'section', 'subject', 'teacher',
            ),
            pk=assignment_id,
            teacher__user=request.user,
            school=school,
        )

        if active_year and assignment.academic_year_id != active_year.id:
            raise NotFound('Teacher assignment not found.')

        date_param = request.query_params.get('date')
        if date_param:
            try:
                target_date = datetime.strptime(date_param, '%Y-%m-%d').date()
            except ValueError:
                raise ValidationError({'date': 'Date must be in YYYY-MM-DD format.'})
        else:
            target_date = timezone.localdate()

        enrollments = list(
            StudentEnrollment.objects.filter(
                school=school,
                academic_year=assignment.academic_year,
                classroom=assignment.classroom,
                section=assignment.section,
                status='active',
                is_current=True,
            ).select_related(
                'student', 'classroom', 'section',
            ).order_by('student__full_name')
        )

        attendances = Attendance.objects.filter(
            student_enrollment__in=enrollments,
            attendance_date=target_date,
        ).select_related('academic_term')

        attendance_map = {att.student_enrollment_id: att for att in attendances}

        roster = []
        for enrollment in enrollments:
            att = attendance_map.get(enrollment.id)
            roster.append({
                'student_enrollment_id': enrollment.id,
                'student': enrollment.student,
                'classroom': enrollment.classroom,
                'section': enrollment.section,
                'attendance': att,
            })

        response_data = {
            'assignment_id': assignment.id,
            'school': assignment.school,
            'academic_year': assignment.academic_year,
            'classroom': assignment.classroom,
            'section': assignment.section,
            'subject': assignment.subject,
            'date': target_date,
            'total_students': len(roster),
            'recorded_count': len(attendance_map),
            'roster': roster,
        }

        serializer = TeacherAssignmentRosterResponseSerializer(
            response_data, context={'request': request},
        )
        return Response(serializer.data, status=status.HTTP_200_OK)
