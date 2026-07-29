from decimal import Decimal

from django.db.models import Avg, Count, Max, Min
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework import generics, status
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from .exam_selectors import (
    exam_result_logs_for_user, exam_results_for_user, exam_types_for_user,
    exams_for_user,
)
from .exam_serializers import (
    BulkGradeSerializer, BulkPublishSerializer, ExamResultLogSerializer, ExamResultSerializer,
    ExamQuerySerializer, ExamResultQuerySerializer, ExamSerializer,
    ExamTypeQuerySerializer, ExamTypeSerializer, PublicationSummarySerializer,
    RejectActionSerializer, WorkflowActionSerializer,
)
from .models import Classroom, ExamResult, ExamResultLog, Subject
from .permissions import (
    IsActiveSchoolUser, IsParent, IsStudent, IsTeacher,
)
from .selectors import students_for_user
from .services.exam_results import (
    approve_exam_result, delete_exam_result, publish_results,
    publish_results_bulk, reject_exam_result, reopen_exam_result,
    submit_exam_result, unpublish_results,
)


MANAGER_ROLES = ('super_admin', 'school_admin', 'teacher')
APPROVER_ROLES = ('super_admin', 'school_admin')


def _require_role(user, roles):
    if user.role not in roles:
        raise PermissionDenied('You do not have permission for this action.')


class ExamTypeListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = ExamTypeSerializer
    permission_classes = [IsActiveSchoolUser]

    @extend_schema(parameters=[ExamTypeQuerySerializer])
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        query = ExamTypeQuerySerializer(data=self.request.query_params)
        query.is_valid(raise_exception=True)
        queryset = exam_types_for_user(self.request.user)
        if 'is_active' in self.request.query_params:
            queryset = queryset.filter(is_active=query.validated_data['is_active'])
        return queryset.order_by('name', 'id')

    def create(self, request, *args, **kwargs):
        _require_role(request.user, APPROVER_ROLES)
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        serializer.save()


class ExamTypeDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ExamTypeSerializer
    permission_classes = [IsActiveSchoolUser]

    def get_queryset(self):
        return exam_types_for_user(self.request.user)

    def update(self, request, *args, **kwargs):
        _require_role(request.user, APPROVER_ROLES)
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        _require_role(request.user, APPROVER_ROLES)
        instance = self.get_object()
        if instance.exams.exists():
            raise ValidationError('Exam types in use cannot be deleted.')
        return super().destroy(request, *args, **kwargs)


class ExamListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = ExamSerializer
    permission_classes = [IsActiveSchoolUser]

    @extend_schema(parameters=[ExamQuerySerializer])
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        query = ExamQuerySerializer(data=self.request.query_params)
        query.is_valid(raise_exception=True)
        params = query.validated_data
        queryset = exams_for_user(self.request.user)
        filters = {
            'academic_year_id': 'academic_year_id',
            'academic_term_id': 'academic_term_id',
            'teacher_assignment_id': 'teacher_assignment_id',
            'exam_type_id': 'exam_type_id',
            'status': 'status',
        }
        for parameter, field in filters.items():
            if parameter in params:
                queryset = queryset.filter(**{field: params[parameter]})
        return queryset.order_by('-exam_date', '-id')

    def create(self, request, *args, **kwargs):
        _require_role(request.user, MANAGER_ROLES)
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        serializer.save()


class ExamDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ExamSerializer
    permission_classes = [IsActiveSchoolUser]

    def get_queryset(self):
        return exams_for_user(self.request.user)

    def update(self, request, *args, **kwargs):
        _require_role(request.user, MANAGER_ROLES)
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        _require_role(request.user, MANAGER_ROLES)
        exam = self.get_object()
        if exam.status != 'draft' or exam.results.exists():
            raise ValidationError('Only empty draft exams can be deleted.')
        return super().destroy(request, *args, **kwargs)


class ExamResultListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = ExamResultSerializer
    permission_classes = [IsActiveSchoolUser]

    @extend_schema(parameters=[ExamResultQuerySerializer])
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        query = ExamResultQuerySerializer(data=self.request.query_params)
        query.is_valid(raise_exception=True)
        params = query.validated_data
        queryset = exam_results_for_user(self.request.user)
        filters = {
            'exam_id': 'exam_id',
            'student_id': 'student_enrollment__student_id',
            'classroom_id': 'student_enrollment__classroom_id',
            'section_id': 'student_enrollment__section_id',
            'subject_id': 'exam__teacher_assignment__subject_id',
            'workflow_status': 'workflow_status',
            'status': 'status',
        }
        for parameter, field in filters.items():
            if parameter in params:
                queryset = queryset.filter(**{field: params[parameter]})
        return queryset.order_by('-exam__exam_date', 'student_enrollment__student__full_name')

    def create(self, request, *args, **kwargs):
        _require_role(request.user, MANAGER_ROLES)
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        serializer.save()


class ExamResultDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ExamResultSerializer
    permission_classes = [IsActiveSchoolUser]

    def get_queryset(self):
        return exam_results_for_user(self.request.user)

    def update(self, request, *args, **kwargs):
        _require_role(request.user, MANAGER_ROLES)
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        _require_role(request.user, MANAGER_ROLES)
        result = self.get_object()
        delete_exam_result(exam_result=result, changed_by=request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)


class BulkGradeAPIView(APIView):
    permission_classes = [IsActiveSchoolUser]
    throttle_scope = 'bulk_results'

    @extend_schema(
        request=BulkGradeSerializer,
        responses={200: ExamResultSerializer(many=True)},
    )
    def post(self, request):
        _require_role(request.user, MANAGER_ROLES)
        serializer = BulkGradeSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        results = serializer.save()
        return Response(ExamResultSerializer(results, many=True).data)


class ExamPublicationAPIView(APIView):
    permission_classes = [IsActiveSchoolUser]
    action = 'publish'

    @extend_schema(
        request=WorkflowActionSerializer,
        responses={
            200: PublicationSummarySerializer,
            400: OpenApiTypes.OBJECT,
            401: OpenApiTypes.OBJECT,
            403: OpenApiTypes.OBJECT,
            404: OpenApiTypes.OBJECT,
        },
        description=(
            'School and super administrators publish or unpublish results in '
            'their tenant scope atomically. Publication skips non-approved '
            'results; unauthenticated, forbidden, and out-of-scope requests '
            'return 401, 403, and 404 respectively.'
        ),
    )
    def post(self, request, pk):
        _require_role(request.user, APPROVER_ROLES)
        exam = generics.get_object_or_404(exams_for_user(request.user), pk=pk)
        serializer = WorkflowActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        service = publish_results if self.action == 'publish' else unpublish_results
        summary = service(
            exam=exam, changed_by=request.user,
            reason=serializer.validated_data.get('reason'), request=request,
        )
        return Response(PublicationSummarySerializer(summary).data)


class PublishExamAPIView(ExamPublicationAPIView):
    pass


class UnpublishExamAPIView(ExamPublicationAPIView):
    action = 'unpublish'


class BulkPublishExamsAPIView(APIView):
    permission_classes = [IsActiveSchoolUser]
    throttle_scope = 'bulk_publish'

    @extend_schema(
        request=BulkPublishSerializer,
        responses={
            200: PublicationSummarySerializer(many=True),
            400: OpenApiTypes.OBJECT,
            401: OpenApiTypes.OBJECT,
            403: OpenApiTypes.OBJECT,
            404: OpenApiTypes.OBJECT,
        },
        description=(
            'Atomically publishes approved results across multiple scoped '
            'exams. Duplicate IDs are rejected and any exam-level error rolls '
            'back the complete request.'
        ),
    )
    def post(self, request):
        _require_role(request.user, APPROVER_ROLES)
        serializer = BulkPublishSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        exam_ids = serializer.validated_data['exam_ids']
        exam_map = {exam.pk: exam for exam in exams_for_user(request.user).filter(pk__in=exam_ids)}
        if len(exam_map) != len(exam_ids):
            raise NotFound('One or more exams were not found.')
        summaries = publish_results_bulk(
            exams=[exam_map[exam_id] for exam_id in exam_ids],
            changed_by=request.user,
            reason=serializer.validated_data.get('reason'), request=request,
        )
        return Response(PublicationSummarySerializer(summaries, many=True).data)


class ResultWorkflowAPIView(APIView):
    permission_classes = [IsActiveSchoolUser]
    action = None
    input_serializer = WorkflowActionSerializer

    @extend_schema(request=WorkflowActionSerializer, responses={200: ExamResultSerializer})
    def post(self, request, pk):
        result = generics.get_object_or_404(exam_results_for_user(request.user), pk=pk)
        serializer = self.input_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        reason = serializer.validated_data.get('reason')
        if self.action == 'submit':
            _require_role(request.user, MANAGER_ROLES)
            result = submit_exam_result(
                exam_result=result, changed_by=request.user, request=request,
            )
        elif self.action == 'approve':
            _require_role(request.user, APPROVER_ROLES)
            result = approve_exam_result(
                exam_result=result, changed_by=request.user, reason=reason, request=request,
            )
        elif self.action == 'reject':
            _require_role(request.user, APPROVER_ROLES)
            result = reject_exam_result(
                exam_result=result, changed_by=request.user, reason=reason, request=request,
            )
        elif self.action == 'reopen':
            _require_role(request.user, APPROVER_ROLES)
            result = reopen_exam_result(
                exam_result=result, changed_by=request.user, reason=reason, request=request,
            )
        return Response(ExamResultSerializer(result).data)


class SubmitResultAPIView(ResultWorkflowAPIView):
    action = 'submit'


class ApproveResultAPIView(ResultWorkflowAPIView):
    action = 'approve'


class RejectResultAPIView(ResultWorkflowAPIView):
    action = 'reject'
    input_serializer = RejectActionSerializer

    @extend_schema(request=RejectActionSerializer, responses={200: ExamResultSerializer})
    def post(self, request, pk):
        return super().post(request, pk)


class ReopenResultAPIView(ResultWorkflowAPIView):
    action = 'reopen'


class ExamResultLogListAPIView(generics.ListAPIView):
    serializer_class = ExamResultLogSerializer
    permission_classes = [IsActiveSchoolUser]
    pagination_class = None

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return ExamResultLog.objects.none()
        _require_role(self.request.user, MANAGER_ROLES)
        result = generics.get_object_or_404(
            exam_results_for_user(self.request.user), pk=self.kwargs['pk'],
        )
        return exam_result_logs_for_user(self.request.user).filter(exam_result=result)


class RoleResultsAPIView(generics.ListAPIView):
    serializer_class = ExamResultSerializer
    permission_classes = [IsActiveSchoolUser]

    def get_queryset(self):
        return exam_results_for_user(self.request.user).order_by('-exam__exam_date', '-id')


class StudentOwnResultsAPIView(RoleResultsAPIView):
    permission_classes = [IsActiveSchoolUser, IsStudent]


class ParentOwnResultsAPIView(RoleResultsAPIView):
    permission_classes = [IsActiveSchoolUser, IsParent]


class TeacherOwnResultsAPIView(RoleResultsAPIView):
    permission_classes = [IsActiveSchoolUser, IsTeacher]


def _statistics(queryset):
    scored = queryset.filter(status='present', score__isnull=False)
    aggregate = scored.aggregate(
        average=Avg('score'), highest=Max('score'), lowest=Min('score'),
    )
    rows = list(scored.values_list('score', 'exam__total_marks'))
    passed = sum(1 for score, total in rows if total and score * 100 >= total * 50)
    total = len(rows)
    distribution = {'0-49': 0, '50-59': 0, '60-69': 0, '70-79': 0, '80-89': 0, '90-100': 0}
    for score, maximum in rows:
        percentage = (score / maximum * Decimal('100')) if maximum else Decimal('0')
        if percentage < 50: key = '0-49'
        elif percentage < 60: key = '50-59'
        elif percentage < 70: key = '60-69'
        elif percentage < 80: key = '70-79'
        elif percentage < 90: key = '80-89'
        else: key = '90-100'
        distribution[key] += 1
    return {
        'total_results': queryset.count(), 'scored_results': total,
        'average': aggregate['average'], 'highest': aggregate['highest'],
        'lowest': aggregate['lowest'], 'pass_count': passed,
        'fail_count': total - passed,
        'pass_rate': round(passed * 100 / total, 2) if total else 0,
        'fail_rate': round((total - passed) * 100 / total, 2) if total else 0,
        'distribution': distribution,
    }


class StudentTranscriptAPIView(APIView):
    permission_classes = [IsActiveSchoolUser]
    throttle_scope = 'reports'

    @extend_schema(responses={200: OpenApiTypes.OBJECT})
    def get(self, request, student_id):
        student = generics.get_object_or_404(students_for_user(request.user), pk=student_id)
        results = exam_results_for_user(request.user).filter(
            student_enrollment__student=student,
        )
        if request.user.role in ('parent', 'student'):
            results = results.filter(workflow_status='approved', is_published=True)
        results = results.order_by('exam__exam_date')
        return Response({
            'student': {'id': student.id, 'name': student.full_name},
            'statistics': _statistics(results),
            'results': ExamResultSerializer(results, many=True).data,
        })


class ScopedSummaryAPIView(APIView):
    permission_classes = [IsActiveSchoolUser]
    throttle_scope = 'reports'
    scope_field = None

    @extend_schema(responses={200: OpenApiTypes.OBJECT})
    def get(self, request, object_id):
        _require_role(request.user, MANAGER_ROLES)
        results = exam_results_for_user(request.user).filter(
            **{self.scope_field: object_id},
        )
        if not results.exists():
            raise NotFound('Report scope not found.')
        return Response({'statistics': _statistics(results)})


class ClassResultSummaryAPIView(ScopedSummaryAPIView):
    scope_field = 'student_enrollment__classroom_id'


class SubjectResultSummaryAPIView(ScopedSummaryAPIView):
    scope_field = 'exam__teacher_assignment__subject_id'


class ExamResultSummaryAPIView(APIView):
    permission_classes = [IsActiveSchoolUser]
    throttle_scope = 'reports'

    @extend_schema(responses={200: OpenApiTypes.OBJECT})
    def get(self, request, exam_id):
        _require_role(request.user, MANAGER_ROLES)
        exam = generics.get_object_or_404(exams_for_user(request.user), pk=exam_id)
        results = exam_results_for_user(request.user).filter(exam=exam)
        return Response({
            'exam': {'id': exam.id, 'title': exam.title},
            'statistics': _statistics(results),
        })