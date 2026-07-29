from django.db.models import Count, Min, Prefetch, Q, Subquery
from rest_framework import generics, status
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from django.utils import timezone

from .models import (
    AcademicTerm,
    Attendance,
    Classroom,
    Parent,
    Section,
    School,
    Student,
    StudentEnrollment,
    StudentGuardian,
    Subject,
    Teacher,
    TeacherAssignment,
)
from .mixins import SchoolQuerySetMixin
from .permissions import (
    IsActiveSchoolUser, IsAttendanceManager, IsParent, IsStudent, IsTeacher,
)
from .selectors import (
    get_attendance_queryset_for_user,
    get_teacher_assignments_for_user,
    students_for_user,
)
from .serializers import (
    AttendanceSerializer,
    BulkAttendanceSerializer,
    LoginTokenObtainPairSerializer,
    LogoutSerializer,
    ParentChildSerializer,
    SchoolSerializer,
    SecureTokenRefreshSerializer,
    StudentDetailSerializer,
    StudentEnrollmentSerializer,
    StudentListSerializer,
    SubjectBriefSerializer,
    TeacherAssignmentSerializer,
    TeacherClassSerializer,
    UserContextSerializer,
)


class LoginTokenObtainPairView(TokenObtainPairView):
    serializer_class = LoginTokenObtainPairSerializer


class SecureTokenRefreshView(TokenRefreshView):
    serializer_class = SecureTokenRefreshSerializer


class LogoutAPIView(APIView):
    permission_classes = [IsActiveSchoolUser]

    def post(self, request):
        serializer = LogoutSerializer(
            data=request.data,
            context={'request': request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(status=status.HTTP_205_RESET_CONTENT)


class CurrentUserAPIView(generics.RetrieveAPIView):
    serializer_class = UserContextSerializer
    permission_classes = [IsActiveSchoolUser]

    def get_object(self):
        return self.request.user


class SchoolListAPIView(SchoolQuerySetMixin, generics.ListAPIView):
    serializer_class = SchoolSerializer
    permission_classes = [IsActiveSchoolUser]

    def get_queryset(self):
        return self.get_school_queryset(School.objects.all().order_by('name'))


class StudentListAPIView(generics.ListAPIView):
    serializer_class = StudentListSerializer
    permission_classes = [IsActiveSchoolUser]

    def get_queryset(self):
        queryset = students_for_user(self.request.user)

        search = self.request.query_params.get('search', '').strip()
        if search:
            queryset = queryset.filter(
                Q(full_name__icontains=search)
                | Q(student_code__icontains=search)
            )

        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            normalized = is_active.lower()
            if normalized in ('true', '1'):
                queryset = queryset.filter(is_active=True)
            elif normalized in ('false', '0'):
                queryset = queryset.filter(is_active=False)

        ordering = self.request.query_params.get('ordering', 'full_name')
        allowed_ordering = {
            'full_name', '-full_name', 'student_code', '-student_code',
            'created_at', '-created_at',
        }
        if ordering not in allowed_ordering:
            ordering = 'full_name'
        return queryset.order_by(ordering)


class StudentDetailAPIView(generics.RetrieveAPIView):
    serializer_class = StudentDetailSerializer
    permission_classes = [IsActiveSchoolUser]

    def get_queryset(self):
        return students_for_user(self.request.user)


class StudentMeProfileAPIView(generics.RetrieveAPIView):
    serializer_class = StudentDetailSerializer
    permission_classes = [IsActiveSchoolUser, IsStudent]

    def get_object(self):
        try:
            return students_for_user(self.request.user).get(user=self.request.user)
        except Student.DoesNotExist as exc:
            raise NotFound('Student profile not found.') from exc


class StudentAcademicHistoryAPIView(generics.ListAPIView):
    serializer_class = StudentEnrollmentSerializer
    permission_classes = [IsActiveSchoolUser]

    def get_queryset(self):
        student = generics.get_object_or_404(
            students_for_user(self.request.user),
            pk=self.kwargs['pk'],
        )
        return student.enrollments.select_related(
            'school', 'academic_year', 'classroom', 'section',
        ).order_by('-academic_year__start_date', '-created_at')


class ParentChildrenAPIView(generics.ListAPIView):
    serializer_class = ParentChildSerializer
    permission_classes = [IsActiveSchoolUser, IsParent]

    def get_queryset(self):
        try:
            parent = Parent.objects.get(
                user=self.request.user,
                school_id=self.request.user.school_id,
            )
        except Parent.DoesNotExist as exc:
            raise NotFound('Parent profile not found.') from exc

        enrollments = StudentEnrollment.objects.select_related(
            'school', 'academic_year', 'classroom', 'section',
        ).order_by('-is_current', '-academic_year__start_date', '-created_at')
        return StudentGuardian.objects.filter(parent=parent).select_related(
            'student', 'student__school',
        ).prefetch_related(
            Prefetch('student__enrollments', queryset=enrollments),
        ).order_by('student__full_name')


def _teacher_for_user(user):
    try:
        return Teacher.objects.get(user=user, school_id=user.school_id)
    except Teacher.DoesNotExist as exc:
        raise NotFound('Teacher profile not found.') from exc


def _current_assignments_for_user(user):
    teacher = _teacher_for_user(user)
    queryset = TeacherAssignment.objects.filter(
        teacher=teacher,
        school_id=user.school_id,
        is_current=True,
    )
    if user.academic_year_id:
        queryset = queryset.filter(academic_year_id=user.academic_year_id)
    else:
        queryset = queryset.filter(academic_year__is_active=True)
    return queryset


class TeacherAssignmentsAPIView(generics.ListAPIView):
    serializer_class = TeacherAssignmentSerializer
    permission_classes = [IsActiveSchoolUser, IsTeacher]

    def get_queryset(self):
        teacher = _teacher_for_user(self.request.user)
        queryset = TeacherAssignment.objects.filter(
            teacher=teacher,
            school_id=self.request.user.school_id,
        )
        if self.request.query_params.get('current', '').lower() in ('true', '1'):
            queryset = _current_assignments_for_user(self.request.user)
        return queryset.select_related(
            'school', 'academic_year', 'classroom', 'section', 'subject',
        ).order_by('-is_current', 'classroom__name', 'section__name', 'subject__name')


class TeacherClassesAPIView(generics.ListAPIView):
    serializer_class = TeacherClassSerializer
    permission_classes = [IsActiveSchoolUser, IsTeacher]

    def get_queryset(self):
        assignments = _current_assignments_for_user(self.request.user)
        unique_ids = assignments.values('classroom_id', 'section_id').annotate(
            first_id=Min('id'),
        ).values('first_id')
        return TeacherAssignment.objects.filter(
            pk__in=Subquery(unique_ids),
        ).select_related('classroom', 'section').order_by(
            'classroom__name', 'section__name',
        )


class TeacherStudentsAPIView(generics.ListAPIView):
    serializer_class = StudentListSerializer
    permission_classes = [IsActiveSchoolUser, IsTeacher]

    def get_queryset(self):
        _teacher_for_user(self.request.user)
        return students_for_user(self.request.user).order_by('full_name')


class TeacherSubjectsAPIView(generics.ListAPIView):
    serializer_class = SubjectBriefSerializer
    permission_classes = [IsActiveSchoolUser, IsTeacher]

    def get_queryset(self):
        assignments = _current_assignments_for_user(self.request.user)
        return Subject.objects.filter(
            teacher_assignments__in=assignments,
        ).distinct().order_by('name')

class AttendanceListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = AttendanceSerializer

    def get_permissions(self):
        classes = [IsActiveSchoolUser]
        if self.request.method == 'POST':
            classes.append(IsAttendanceManager)
        return [permission() for permission in classes]

    def get_queryset(self):
        queryset = get_attendance_queryset_for_user(self.request.user)
        params = self.request.query_params
        field_filters = {
            'attendance_date': 'attendance_date',
            'status': 'status',
            'student_enrollment': 'student_enrollment_id',
            'teacher_assignment': 'teacher_assignment_id',
            'classroom': 'student_enrollment__classroom_id',
            'section': 'student_enrollment__section_id',
            'academic_year': 'student_enrollment__academic_year_id',
            'academic_term': 'academic_term_id',
        }
        for parameter, field in field_filters.items():
            value = params.get(parameter)
            if value:
                queryset = queryset.filter(**{field: value})
        search = params.get('search', '').strip()
        if search:
            queryset = queryset.filter(
                Q(student_enrollment__student__full_name__icontains=search)
                | Q(student_enrollment__student__student_code__icontains=search)
            )
        ordering = params.get('ordering', '-attendance_date')
        if ordering not in {
            'attendance_date', '-attendance_date', 'created_at', '-created_at',
        }:
            ordering = '-attendance_date'
        return queryset.order_by(ordering, 'id')


class AttendanceDetailAPIView(generics.RetrieveUpdateAPIView):
    serializer_class = AttendanceSerializer

    def get_permissions(self):
        classes = [IsActiveSchoolUser]
        if self.request.method in ('PUT', 'PATCH'):
            classes.append(IsAttendanceManager)
        return [permission() for permission in classes]

    def get_queryset(self):
        return get_attendance_queryset_for_user(self.request.user)


class BulkAttendanceAPIView(APIView):
    permission_classes = [IsActiveSchoolUser, IsAttendanceManager]

    def post(self, request):
        serializer = BulkAttendanceSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        from .services.attendance import save_bulk_attendance
        result = save_bulk_attendance(
            teacher_assignment=serializer.validated_data['teacher_assignment'],
            academic_term=serializer.validated_data['academic_term'],
            attendance_date=serializer.validated_data['attendance_date'],
            students=serializer.validated_data['students'],
        )
        return Response({
            'success': True,
            'created': result['created'],
            'updated': result['updated'],
            'total': result['total'],
            'records': AttendanceSerializer(
                result['records'], many=True, context={'request': request},
            ).data,
        }, status=status.HTTP_200_OK)


def _date_range(queryset, params):
    date_from = params.get('date_from')
    date_to = params.get('date_to')
    if date_from:
        queryset = queryset.filter(attendance_date__gte=date_from)
    if date_to:
        queryset = queryset.filter(attendance_date__lte=date_to)
    return queryset


def _status_counts(queryset):
    counts = {choice: 0 for choice, _ in Attendance.STATUS_CHOICES}
    for item in queryset.values('status').annotate(total=Count('id')):
        counts[item['status']] = item['total']
    return counts


def _percentage(counts, total):
    attended = counts.get('present', 0) + counts.get('late', 0)
    return round((attended / total) * 100, 2) if total else 0.0


class DailyAttendanceReportAPIView(APIView):
    permission_classes = [IsActiveSchoolUser, IsAttendanceManager]

    def get(self, request):
        report_date = (
            request.query_params.get('date')
            or timezone.localdate().isoformat()
        )
        summary_records = get_attendance_queryset_for_user(request.user).filter(
            attendance_date=report_date,
        )
        assignment_id = request.query_params.get('teacher_assignment_id')
        classroom_id = request.query_params.get('classroom_id')
        section_id = request.query_params.get('section_id')
        status_filter = request.query_params.get('status')

        assignments = get_teacher_assignments_for_user(request.user)
        if request.user.role == 'teacher':
            assignments = assignments.filter(is_current=True)
            if request.user.academic_year_id:
                assignments = assignments.filter(
                    academic_year_id=request.user.academic_year_id,
                )
        if assignment_id:
            assignments = assignments.filter(pk=assignment_id)
            if not assignments.exists():
                raise NotFound('Teacher assignment not found.')
            summary_records = summary_records.filter(
                teacher_assignment_id=assignment_id,
            )
        if classroom_id:
            summary_records = summary_records.filter(
                student_enrollment__classroom_id=classroom_id,
            )
        if section_id:
            summary_records = summary_records.filter(
                student_enrollment__section_id=section_id,
            )

        expected = StudentEnrollment.objects.filter(
            status='active', is_current=True,
        )
        if assignment_id or request.user.role == 'teacher':
            if classroom_id:
                assignments = assignments.filter(classroom_id=classroom_id)
            if section_id:
                assignments = assignments.filter(section_id=section_id)
            scope = Q()
            assignment_ids = []
            for assignment in assignments.values(
                'id', 'academic_year_id', 'classroom_id', 'section_id',
            ):
                assignment_ids.append(assignment['id'])
                scope |= Q(
                    academic_year_id=assignment['academic_year_id'],
                    classroom_id=assignment['classroom_id'],
                    section_id=assignment['section_id'],
                )
            expected = (
                expected.none()
                if not scope
                else expected.filter(scope)
            )
            if request.user.role == 'teacher':
                summary_records = summary_records.filter(
                    teacher_assignment_id__in=assignment_ids,
                )
        else:
            if request.user.role == 'school_admin':
                expected = expected.filter(school_id=request.user.school_id)
            if classroom_id:
                expected = expected.filter(classroom_id=classroom_id)
            if section_id:
                expected = expected.filter(section_id=section_id)

        total_students = expected.values('student_id').distinct().count()
        recorded = summary_records.values(
            'student_enrollment__student_id',
        ).distinct().count()
        counts = _status_counts(summary_records)
        displayed_records = summary_records
        records_filter = {}
        if status_filter:
            displayed_records = displayed_records.filter(status=status_filter)
            records_filter['status'] = status_filter

        return Response({
            'date': report_date,
            'total_students': total_students,
            'recorded': recorded,
            **{key: counts[key] for key, _ in Attendance.STATUS_CHOICES},
            'not_recorded': max(total_students - recorded, 0),
            'records_filter': records_filter,
            'records': AttendanceSerializer(
                displayed_records.order_by('id'),
                many=True,
                context={'request': request},
            ).data,
        })

class StudentAttendanceSummaryAPIView(APIView):
    permission_classes = [IsActiveSchoolUser]

    def get(self, request, student_id):
        student = generics.get_object_or_404(students_for_user(request.user), pk=student_id)
        records = get_attendance_queryset_for_user(request.user).filter(
            student_enrollment__student=student,
        )
        records = _date_range(records, request.query_params)
        if request.query_params.get('academic_year_id'):
            records = records.filter(
                student_enrollment__academic_year_id=request.query_params['academic_year_id'],
            )
        if request.query_params.get('academic_term_id'):
            records = records.filter(academic_term_id=request.query_params['academic_term_id'])
        counts = _status_counts(records)
        total = records.count()
        return Response({
            'student': {'id': student.id, 'student_code': student.student_code, 'full_name': student.full_name},
            'period': {
                'date_from': request.query_params.get('date_from'),
                'date_to': request.query_params.get('date_to'),
            },
            'total_records': total,
            **{f'{key}_count': counts[key] for key, _ in Attendance.STATUS_CHOICES},
            'attendance_percentage': _percentage(counts, total),
            'records': AttendanceSerializer(records.order_by('-attendance_date'), many=True, context={'request': request}).data,
        })


class ClassAttendanceSummaryAPIView(APIView):
    permission_classes = [IsActiveSchoolUser, IsAttendanceManager]

    def get(self, request, classroom_id):
        classrooms = Classroom.objects.select_related('school', 'academic_year').filter(pk=classroom_id)
        if request.user.role != 'super_admin':
            classrooms = classrooms.filter(school_id=request.user.school_id)
        classroom = classrooms.first()
        if classroom is None:
            raise NotFound('Classroom not found.')

        section_id = request.query_params.get('section_id')
        if section_id:
            section = Section.objects.filter(
                pk=section_id,
                classroom=classroom,
                school=classroom.school,
            ).first()
            if section is None:
                raise NotFound('Section not found.')

        assignments = get_teacher_assignments_for_user(request.user).filter(
            classroom=classroom,
        )
        if request.user.role == 'teacher':
            assignments = assignments.filter(is_current=True)
            if request.user.academic_year_id:
                assignments = assignments.filter(
                    academic_year_id=request.user.academic_year_id,
                )
        assignment_id = request.query_params.get('teacher_assignment_id')
        if section_id:
            assignments = assignments.filter(section_id=section_id)
        if assignment_id:
            assignments = assignments.filter(pk=assignment_id)
        if request.user.role == 'teacher' and not assignments.exists():
            raise NotFound('Classroom not found.')
        if assignment_id and not assignments.exists():
            raise NotFound('Teacher assignment not found.')

        enrollments = StudentEnrollment.objects.filter(
            classroom=classroom, status='active', is_current=True,
        ).select_related('student', 'section')
        if section_id:
            enrollments = enrollments.filter(section_id=section_id)
        if request.user.role == 'teacher':
            enrollments = enrollments.filter(section_id__in=assignments.values('section_id'))

        records = get_attendance_queryset_for_user(request.user).filter(
            student_enrollment__in=enrollments,
        )
        records = _date_range(records, request.query_params)
        if request.query_params.get('academic_year_id'):
            records = records.filter(student_enrollment__academic_year_id=request.query_params['academic_year_id'])
        if request.query_params.get('academic_term_id'):
            records = records.filter(academic_term_id=request.query_params['academic_term_id'])
        if assignment_id:
            records = records.filter(teacher_assignment_id=assignment_id)

        totals = _status_counts(records)
        per_student = {}
        for row in records.values(
            'student_enrollment__student_id', 'status',
        ).annotate(total=Count('id')):
            student_id = row['student_enrollment__student_id']
            per_student.setdefault(student_id, {})[row['status']] = row['total']

        enrollment_list = list(enrollments.order_by('student__full_name'))
        students_summary = []
        for enrollment in enrollment_list:
            stored_counts = per_student.get(enrollment.student_id, {})
            student_counts = {
                choice: stored_counts.get(choice, 0)
                for choice, _ in Attendance.STATUS_CHOICES
            }
            student_total = sum(student_counts.values())
            students_summary.append({
                'student': {'id': enrollment.student_id, 'student_code': enrollment.student.student_code, 'full_name': enrollment.student.full_name},
                **{f'{key}_count': student_counts[key] for key, _ in Attendance.STATUS_CHOICES},
                'attendance_percentage': _percentage(student_counts, student_total),
            })
        return Response({
            'classroom': {'id': classroom.id, 'name': classroom.name, 'code': classroom.code},
            'section': int(section_id) if section_id else None,
            'period': {'date_from': request.query_params.get('date_from'), 'date_to': request.query_params.get('date_to')},
            'total_students': len({item.student_id for item in enrollment_list}),
            'total_attendance_records': records.count(),
            'status_totals': totals,
            'students_summary': students_summary,
        })
