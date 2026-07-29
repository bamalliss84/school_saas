from django.db.models import Min, Prefetch, Q, Subquery
from rest_framework import generics, status
from rest_framework.exceptions import NotFound
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .models import (
    Parent,
    School,
    Student,
    StudentEnrollment,
    StudentGuardian,
    Subject,
    Teacher,
    TeacherAssignment,
)
from .mixins import SchoolQuerySetMixin
from .permissions import IsActiveSchoolUser, IsParent, IsStudent, IsTeacher
from .selectors import students_for_user
from .serializers import (
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