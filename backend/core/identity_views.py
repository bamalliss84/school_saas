from collections import OrderedDict

from drf_spectacular.utils import extend_schema
from rest_framework import generics, status
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView

from .context import get_active_membership, get_user_memberships
from .identity_serializers import (
    AcademicHistoryQuerySerializer, StudentSchoolHistorySerializer,
    StudentTransferSerializer,
)
from .models import SchoolMembership, Student, StudentEnrollment
from .permissions import IsActiveSchoolUser
from .serializers import StudentEnrollmentSerializer
from .services.identity import transfer_student


def _student_for_self(user):
    try:
        return Student.objects.get(user=user)
    except Student.DoesNotExist as exc:
        raise NotFound('Student profile not found.') from exc


def _parent_child(user, student_id):
    student = Student.objects.filter(
        pk=student_id, guardians__parent__user=user,
    ).distinct().first()
    if student is None:
        raise NotFound('Student was not found.')
    return student


def _membership_for_history(request, role, student):
    query = AcademicHistoryQuerySerializer(data=request.query_params)
    query.is_valid(raise_exception=True)
    params = query.validated_data
    memberships = get_user_memberships(request.user, include_ended=True).filter(role=role)
    membership = get_active_membership(request)
    if params.get('school_membership_id'):
        membership = memberships.filter(pk=params['school_membership_id']).first()
    elif params.get('school_id'):
        membership = memberships.filter(school_id=params['school_id']).first()
    if membership is None or not student.enrollments.filter(school_id=membership.school_id).exists():
        raise NotFound('School history was not found.')
    return membership, params


def _history_queryset(student, school_id, params):
    queryset = student.enrollments.filter(school_id=school_id).select_related(
        'school', 'academic_year', 'classroom', 'section',
    )
    if params.get('academic_year_id'):
        queryset = queryset.filter(academic_year_id=params['academic_year_id'])
    return queryset.order_by('-is_current', '-academic_year__start_date', '-created_at')


def _school_history(student, user, role):
    memberships = {
        item.school_id: item for item in get_user_memberships(
            user, include_ended=True,
        ).filter(role=role)
    }
    grouped = OrderedDict()
    enrollments = student.enrollments.select_related('school', 'academic_year').order_by(
        '-is_current', '-academic_year__start_date',
    )
    for enrollment in enrollments:
        membership = memberships.get(enrollment.school_id)
        if membership is None:
            continue
        row = grouped.setdefault(enrollment.school_id, {
            'school': {'id': enrollment.school_id, 'name': enrollment.school.name},
            'access_mode': 'read_write' if membership.status == 'active' else 'read_only',
            'is_current': enrollment.is_current and enrollment.status == 'active',
            'membership_id': membership.pk,
            'academic_years': [],
        })
        row['academic_years'].append({
            'id': enrollment.academic_year_id, 'name': enrollment.academic_year.name,
            'status': enrollment.status, 'is_current': enrollment.is_current,
        })
    return list(grouped.values())


class StudentMeSchoolsAPIView(APIView):
    permission_classes = (IsActiveSchoolUser,)

    @extend_schema(responses={200: StudentSchoolHistorySerializer(many=True)})
    def get(self, request):
        student = _student_for_self(request.user)
        return Response(_school_history(student, request.user, 'student'))


class StudentMeAcademicHistoryAPIView(APIView):
    permission_classes = (IsActiveSchoolUser,)

    @extend_schema(parameters=[AcademicHistoryQuerySerializer], responses={200: StudentEnrollmentSerializer(many=True)})
    def get(self, request):
        student = _student_for_self(request.user)
        membership, params = _membership_for_history(request, 'student', student)
        return Response(StudentEnrollmentSerializer(
            _history_queryset(student, membership.school_id, params), many=True,
        ).data)


class ParentChildSchoolsAPIView(APIView):
    permission_classes = (IsActiveSchoolUser,)

    @extend_schema(responses={200: StudentSchoolHistorySerializer(many=True)})
    def get(self, request, student_id):
        student = _parent_child(request.user, student_id)
        return Response(_school_history(student, request.user, 'parent'))


class ParentChildAcademicHistoryAPIView(APIView):
    permission_classes = (IsActiveSchoolUser,)

    @extend_schema(parameters=[AcademicHistoryQuerySerializer], responses={200: StudentEnrollmentSerializer(many=True)})
    def get(self, request, student_id):
        student = _parent_child(request.user, student_id)
        membership, params = _membership_for_history(request, 'parent', student)
        return Response(StudentEnrollmentSerializer(
            _history_queryset(student, membership.school_id, params), many=True,
        ).data)


class StudentTransferAPIView(APIView):
    permission_classes = (IsActiveSchoolUser,)

    @extend_schema(request=StudentTransferSerializer, responses={201: StudentEnrollmentSerializer})
    def post(self, request, pk):
        if not (request.user.is_superuser or request.user.role == 'super_admin'):
            raise PermissionDenied('Only a super administrator can transfer students.')
        student = generics.get_object_or_404(Student.objects.all(), pk=pk)
        serializer = StudentTransferSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        enrollment = transfer_student(
            student=student, actor=request.user, request=request,
            **serializer.validated_data,
        )
        return Response(StudentEnrollmentSerializer(enrollment).data, status=status.HTTP_201_CREATED)