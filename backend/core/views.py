from django.db.models import Count, Min, Prefetch, Q, Subquery
from django.utils import timezone
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework import generics, status
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

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
from .query_serializers import (
    AttendanceListQuerySerializer,
    ClassAttendanceSummaryQuerySerializer,
    DailyAttendanceReportQuerySerializer,
    StudentAttendanceSummaryQuerySerializer,
    StudentListQuerySerializer,
    TeacherAssignmentQuerySerializer,
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
    throttle_scope = 'login'


class SecureTokenRefreshView(TokenRefreshView):
    serializer_class = SecureTokenRefreshSerializer
    throttle_scope = 'refresh'


class LogoutAPIView(APIView):
    permission_classes = [IsActiveSchoolUser]
    throttle_scope = 'logout'

    @extend_schema(request=LogoutSerializer, responses={205: None})
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

    @extend_schema(parameters=[StudentListQuerySerializer])
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        query = StudentListQuerySerializer(data=self.request.query_params)
        query.is_valid(raise_exception=True)
        params = query.validated_data
        queryset = students_for_user(self.request.user)

        search = params.get('search', '').strip()
        if search:
            queryset = queryset.filter(
                Q(full_name__icontains=search)
                | Q(student_code__icontains=search)
            )
        if 'is_active' in self.request.query_params:
            queryset = queryset.filter(is_active=params['is_active'])
        if 'school_id' in self.request.query_params:
            if (
                self.request.user.role != 'super_admin'
                and params['school_id'] != self.request.user.school_id
            ):
                raise ValidationError({'school_id': 'School is outside your scope.'})
            queryset = queryset.filter(school_id=params['school_id'])

        enrollment_filters = {
            'academic_year_id': 'enrollments__academic_year_id',
            'classroom_id': 'enrollments__classroom_id',
            'section_id': 'enrollments__section_id',
            'enrollment_status': 'enrollments__status',
            'is_current': 'enrollments__is_current',
        }
        for parameter, field in enrollment_filters.items():
            if parameter in self.request.query_params:
                queryset = queryset.filter(**{field: params[parameter]})
        return queryset.distinct().order_by(params['ordering'])

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
        if getattr(self, 'swagger_fake_view', False):
            return StudentEnrollment.objects.none()
        student = generics.get_object_or_404(
            students_for_user(self.request.user),
            pk=self.kwargs['pk'],
        )
        queryset = student.enrollments.select_related(
            'school', 'academic_year', 'classroom', 'section',
        )
        if self.request.user.role != 'super_admin':
            queryset = queryset.filter(school_id=self.request.user.school_id)
        return queryset.order_by('-academic_year__start_date', '-created_at')


class ParentChildrenAPIView(generics.ListAPIView):
    serializer_class = ParentChildSerializer
    permission_classes = [IsActiveSchoolUser, IsParent]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return StudentGuardian.objects.none()
        try:
            parent = Parent.objects.get(user=self.request.user)
        except Parent.DoesNotExist as exc:
            raise NotFound('Parent profile not found.') from exc

        enrollments = StudentEnrollment.objects.select_related(
            'school', 'academic_year', 'classroom', 'section',
        ).order_by('-is_current', '-academic_year__start_date', '-created_at')
        return StudentGuardian.objects.filter(
            parent=parent, student__enrollments__school_id=self.request.user.school_id,
        ).distinct().select_related(
            'student', 'student__school',
        ).prefetch_related(
            Prefetch('student__enrollments', queryset=enrollments),
        ).order_by('student__full_name')


from .teacher_views import (
    TeacherAssignmentStudentsAPIView,
    TeacherAssignmentsAPIView,
    TeacherClassesAPIView,
    TeacherMeProfileAPIView,
    TeacherStudentsAPIView,
    TeacherSubjectsAPIView,
    _current_assignments_for_request,
    _get_active_academic_year,
    _get_active_school,
    _get_teacher_for_request,
)


def _teacher_for_user(user):
    try:
        return Teacher.objects.get(user=user)
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


class AttendanceListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = AttendanceSerializer

    def get_permissions(self):
        classes = [IsActiveSchoolUser]
        if self.request.method == 'POST':
            classes.append(IsAttendanceManager)
        return [permission() for permission in classes]

    @extend_schema(parameters=[AttendanceListQuerySerializer])
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        query = AttendanceListQuerySerializer(data=self.request.query_params)
        query.is_valid(raise_exception=True)
        params = query.validated_data
        queryset = get_attendance_queryset_for_user(self.request.user, request=self.request)
        field_filters = {
            'attendance_date': 'attendance_date',
            'student_id': 'student_enrollment__student_id',
            'student_enrollment_id': 'student_enrollment_id',
            'teacher_assignment_id': 'teacher_assignment_id',
            'academic_year_id': 'student_enrollment__academic_year_id',
            'academic_term_id': 'academic_term_id',
            'classroom_id': 'student_enrollment__classroom_id',
            'section_id': 'student_enrollment__section_id',
            'status': 'status',
        }
        for parameter, field in field_filters.items():
            if parameter in params:
                queryset = queryset.filter(**{field: params[parameter]})
        if params.get('date_from'):
            queryset = queryset.filter(attendance_date__gte=params['date_from'])
        if params.get('date_to'):
            queryset = queryset.filter(attendance_date__lte=params['date_to'])
        search = params.get('search', '').strip()
        if search:
            queryset = queryset.filter(
                Q(student_enrollment__student__full_name__icontains=search)
                | Q(student_enrollment__student__student_code__icontains=search)
            )
        return queryset.order_by(params['ordering'], 'id')

    def perform_create(self, serializer):
        from .context import require_writable_context
        require_writable_context(self.request)
        serializer.save()


class AttendanceDetailAPIView(generics.RetrieveUpdateAPIView):
    serializer_class = AttendanceSerializer

    def get_permissions(self):
        classes = [IsActiveSchoolUser]
        if self.request.method in ('PUT', 'PATCH'):
            classes.append(IsAttendanceManager)
        return [permission() for permission in classes]

    def get_queryset(self):
        return get_attendance_queryset_for_user(self.request.user, request=self.request)

    def perform_update(self, serializer):
        from .context import require_writable_context
        require_writable_context(self.request)
        serializer.save()


class BulkAttendanceAPIView(APIView):
    permission_classes = [IsActiveSchoolUser, IsAttendanceManager]
    throttle_scope = 'bulk_attendance'

    @extend_schema(
        request=BulkAttendanceSerializer,
        responses={200: OpenApiTypes.OBJECT},
    )
    def post(self, request):
        from .context import require_writable_context
        require_writable_context(request)

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
    throttle_scope = 'reports'

    @extend_schema(
        parameters=[DailyAttendanceReportQuerySerializer],
        responses={200: OpenApiTypes.OBJECT},
    )
    def get(self, request):
        query = DailyAttendanceReportQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        params = query.validated_data
        report_date = params.get('date') or timezone.localdate()
        summary_records = get_attendance_queryset_for_user(request.user).filter(
            attendance_date=report_date,
        )
        assignment_id = params.get('teacher_assignment_id')
        classroom_id = params.get('classroom_id')
        section_id = params.get('section_id')
        status_filter = params.get('status')

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
    throttle_scope = 'reports'

    @extend_schema(
        parameters=[StudentAttendanceSummaryQuerySerializer],
        responses={200: OpenApiTypes.OBJECT},
    )
    def get(self, request, student_id):
        query = StudentAttendanceSummaryQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        params = query.validated_data
        student = generics.get_object_or_404(
            students_for_user(request.user), pk=student_id,
        )
        records = get_attendance_queryset_for_user(request.user).filter(
            student_enrollment__student=student,
        )
        records = _date_range(records, params)
        if params.get('academic_year_id'):
            records = records.filter(
                student_enrollment__academic_year_id=params['academic_year_id'],
            )
        if params.get('academic_term_id'):
            records = records.filter(academic_term_id=params['academic_term_id'])
        counts = _status_counts(records)
        total = records.count()
        return Response({
            'student': {'id': student.id, 'student_code': student.student_code, 'full_name': student.full_name},
            'period': {
                'date_from': params.get('date_from'),
                'date_to': params.get('date_to'),
            },
            'total_records': total,
            **{f'{key}_count': counts[key] for key, _ in Attendance.STATUS_CHOICES},
            'attendance_percentage': _percentage(counts, total),
            'records': AttendanceSerializer(records.order_by('-attendance_date'), many=True, context={'request': request}).data,
        })


class StudentOwnAttendanceAPIView(APIView):
    """Read-only attendance feed for the active student membership context.

    This endpoint is intentionally self-scoped so Flutter never has to trust or
    persist a student id. The selected membership and academic year remain the
    source of truth for current and historical contexts.
    """
    permission_classes = [IsActiveSchoolUser, IsStudent]
    throttle_scope = 'reports'

    @extend_schema(
        parameters=[StudentAttendanceSummaryQuerySerializer],
        responses={200: OpenApiTypes.OBJECT},
    )
    def get(self, request):
        query = StudentAttendanceSummaryQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        params = query.validated_data

        school = request.active_school
        academic_year = request.active_academic_year
        if school is None or academic_year is None:
            raise NotFound('Academic year was not found.')

        student = generics.get_object_or_404(
            Student.objects.filter(user=request.user),
        )
        enrollment = generics.get_object_or_404(
            StudentEnrollment.objects.select_related(
                'school', 'academic_year', 'classroom', 'section',
            ),
            student=student, school=school, academic_year=academic_year,
        )

        records = Attendance.objects.select_related(
            'student_enrollment', 'student_enrollment__student',
            'student_enrollment__school', 'student_enrollment__academic_year',
            'student_enrollment__classroom', 'student_enrollment__section',
            'teacher_assignment', 'academic_term',
        ).filter(student_enrollment=enrollment)
        records = _date_range(records, params)
        if params.get('academic_term_id'):
            records = records.filter(academic_term_id=params['academic_term_id'])

        counts = _status_counts(records)
        total = records.count()
        terms = AcademicTerm.objects.filter(
            school=school, academic_year=academic_year,
        ).order_by('start_date', 'pk')
        return Response({
            'student': {
                'id': student.id,
                'student_code': student.student_code,
                'full_name': student.full_name,
            },
            'academic_year': {
                'id': academic_year.id,
                'name': academic_year.name,
                'start_date': academic_year.start_date,
                'end_date': academic_year.end_date,
            },
            'period': {
                'date_from': params.get('date_from'),
                'date_to': params.get('date_to'),
                'academic_term_id': params.get('academic_term_id'),
            },
            'terms': [
                {
                    'id': term.id,
                    'name': term.name,
                    'term_type': term.term_type,
                    'start_date': term.start_date,
                    'end_date': term.end_date,
                    'is_active': term.is_active,
                }
                for term in terms
            ],
            'total_records': total,
            **{f'{key}_count': counts[key] for key, _ in Attendance.STATUS_CHOICES},
            'attendance_percentage': _percentage(counts, total),
            'records': AttendanceSerializer(
                records.order_by('-attendance_date', '-id'),
                many=True, context={'request': request},
            ).data,
        })


class ClassAttendanceSummaryAPIView(APIView):
    permission_classes = [IsActiveSchoolUser, IsAttendanceManager]
    throttle_scope = 'reports'

    @extend_schema(
        parameters=[ClassAttendanceSummaryQuerySerializer],
        responses={200: OpenApiTypes.OBJECT},
    )
    def get(self, request, classroom_id):
        query = ClassAttendanceSummaryQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        params = query.validated_data
        classrooms = Classroom.objects.select_related(
            'school', 'academic_year',
        ).filter(pk=classroom_id)
        if request.user.role != 'super_admin':
            classrooms = classrooms.filter(school_id=request.user.school_id)
        classroom = classrooms.first()
        if classroom is None:
            raise NotFound('Classroom not found.')

        section_id = params.get('section_id')
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
        assignment_id = params.get('teacher_assignment_id')
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
        records = _date_range(records, params)
        if params.get('academic_year_id'):
            records = records.filter(student_enrollment__academic_year_id=params['academic_year_id'])
        if params.get('academic_term_id'):
            records = records.filter(academic_term_id=params['academic_term_id'])
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
            'period': {'date_from': params.get('date_from'), 'date_to': params.get('date_to')},
            'total_students': len({item.student_id for item in enrollment_list}),
            'total_attendance_records': records.count(),
            'status_totals': totals,
            'students_summary': students_summary,
        })
