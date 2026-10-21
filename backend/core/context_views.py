from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .context import get_active_membership, get_user_memberships
from .models import AcademicYear, StudentEnrollment
from .context_serializers import (
    ContextListSerializer, DefaultContextSerializer, SchoolMembershipSerializer,
)
from .permissions import IsActiveSchoolUser
from .services.notifications import get_context_unread_counts
from .services.messaging import get_context_unread_conversation_counts


class ContextListAPIView(APIView):
    permission_classes = (IsActiveSchoolUser,)

    @extend_schema(responses={200: ContextListSerializer})
    def get(self, request):
        active_id = getattr(getattr(request, 'active_membership', None), 'pk', None)
        memberships = list(get_user_memberships(request.user))
        current = next((item for item in memberships if item.pk == active_id), None)
        notification_counts = get_context_unread_counts(memberships)
        conversation_counts = get_context_unread_conversation_counts(memberships)
        school_ids = {item.school_id for item in memberships}
        active_years = {}
        for year in AcademicYear.objects.filter(school_id__in=school_ids, is_active=True).order_by('school_id', '-start_date', '-pk'):
            active_years.setdefault(year.school_id, {'id': year.pk, 'name': year.name})
        student_years = {}
        student_pairs = {(item.user_id, item.school_id) for item in memberships if item.role == 'student'}
        if student_pairs:
            for enrollment in StudentEnrollment.objects.filter(
                student__user_id__in={pair[0] for pair in student_pairs}, school_id__in=school_ids,
            ).select_related('academic_year').order_by('student__user_id', 'school_id', '-is_current', '-academic_year__start_date'):
                student_years.setdefault((enrollment.student.user_id, enrollment.school_id), {'id': enrollment.academic_year_id, 'name': enrollment.academic_year.name})
        academic_year_map = {item.pk: student_years.get((item.user_id, item.school_id), active_years.get(item.school_id)) if item.role == 'student' else active_years.get(item.school_id) for item in memberships}
        serializer_context = {'request': request, 'notification_counts': notification_counts, 'conversation_counts': conversation_counts, 'academic_year_map': academic_year_map}
        payload = {
            'current_context': SchoolMembershipSerializer(
                current, context=serializer_context,
            ).data if current else None,
            'contexts': SchoolMembershipSerializer(
                memberships, many=True, context=serializer_context,
            ).data,
        }
        return Response(payload)


class CurrentContextAPIView(APIView):
    permission_classes = (IsActiveSchoolUser,)

    @extend_schema(responses={200: SchoolMembershipSerializer})
    def get(self, request):
        membership = get_active_membership(request)
        return Response(SchoolMembershipSerializer(
            membership, context={'request': request},
        ).data if membership else None)


class DefaultContextAPIView(APIView):
    permission_classes = (IsActiveSchoolUser,)

    @extend_schema(request=DefaultContextSerializer, responses={200: SchoolMembershipSerializer})
    def post(self, request):
        serializer = DefaultContextSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        membership = serializer.save()
        return Response(
            SchoolMembershipSerializer(membership, context={'request': request}).data,
            status=status.HTTP_200_OK,
        )