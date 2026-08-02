from datetime import timedelta
from django.db.models import Avg, Count, Max, Min, Q
from django.utils import timezone
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework import generics, status
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from .homework_selectors import homework_for_user, submissions_for_user
from .homework_serializers import (
    AttachmentUploadSerializer, BulkGradeSubmissionsSerializer,
    BulkHomeworkSerializer, GradeSubmissionSerializer, HomeworkAttachmentSerializer,
    HomeworkQuerySerializer, HomeworkReportQuerySerializer, HomeworkSerializer,
    HomeworkSubmissionSerializer,
    ReturnSubmissionSerializer, SubmissionAnswerSerializer,
    SubmissionAttachmentSerializer, SubmissionQuerySerializer,
)
from .models import (
    Classroom, Homework, HomeworkAttachment, HomeworkSubmission,
    HomeworkSubmissionAttachment, Student,
    StudentEnrollment,
)
from .permissions import IsActiveSchoolUser
from .selectors import students_for_user
from .services.homework import (
    add_homework_attachment, add_submission_attachment, bulk_close_homework,
    bulk_grade_submissions, bulk_publish_homework, close_homework,
    create_submission_draft, delete_homework_attachment,
    delete_submission_attachment, final_submit_homework, grade_submission,
    publish_homework, return_submission, update_submission_draft,
)

MANAGER_ROLES = ('super_admin', 'school_admin', 'teacher')


def _require_role(user, roles):
    if user.role not in roles:
        raise PermissionDenied('You do not have permission for this action.')


def _filter_homework(queryset, params, user):
    mapping = {
        'status': 'status', 'academic_year_id': 'academic_year_id',
        'academic_term_id': 'academic_term_id',
        'teacher_assignment_id': 'teacher_assignment_id',
        'classroom_id': 'teacher_assignment__classroom_id',
        'section_id': 'teacher_assignment__section_id',
        'subject_id': 'teacher_assignment__subject_id',
    }
    for parameter, field in mapping.items():
        if parameter in params:
            queryset = queryset.filter(**{field: params[parameter]})
    if params.get('publish_from'):
        queryset = queryset.filter(published_at__gte=params['publish_from'])
    if params.get('publish_to'):
        queryset = queryset.filter(published_at__lte=params['publish_to'])
    if params.get('due_from'):
        queryset = queryset.filter(due_date__gte=params['due_from'])
    if params.get('due_to'):
        queryset = queryset.filter(due_date__lte=params['due_to'])
    if params.get('overdue') is not None:
        lookup = {'due_date__lt': timezone.now()}
        queryset = queryset.filter(**lookup) if params['overdue'] else queryset.exclude(**lookup)
    if params.get('search'):
        queryset = queryset.filter(
            Q(title__icontains=params['search']) | Q(description__icontains=params['search']),
        )
    if params.get('has_submission') is not None:
        own = Q(submissions__isnull=False)
        if user.role == 'student':
            own &= Q(submissions__student_enrollment__student__user=user)
        queryset = queryset.filter(own) if params['has_submission'] else queryset.exclude(own)
    if params.get('submission_status'):
        queryset = queryset.filter(submissions__status=params['submission_status'])
        if user.role == 'student':
            queryset = queryset.filter(submissions__student_enrollment__student__user=user)
    return queryset.distinct().order_by(params['ordering'])


class HomeworkListCreateAPIView(generics.ListCreateAPIView):
    queryset = Homework.objects.none()
    serializer_class = HomeworkSerializer
    permission_classes = (IsActiveSchoolUser,)
    throttle_scope = 'homework_write'

    @extend_schema(parameters=[HomeworkQuerySerializer])
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        query = HomeworkQuerySerializer(data=self.request.query_params)
        query.is_valid(raise_exception=True)
        return _filter_homework(homework_for_user(self.request.user, self.request), query.validated_data, self.request.user)

    def create(self, request, *args, **kwargs):
        _require_role(request.user, MANAGER_ROLES)
        return super().create(request, *args, **kwargs)


class HomeworkDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = HomeworkSerializer
    permission_classes = (IsActiveSchoolUser,)
    throttle_scope = 'homework_write'

    def get_queryset(self):
        return homework_for_user(self.request.user, self.request)

    def update(self, request, *args, **kwargs):
        _require_role(request.user, MANAGER_ROLES)
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        _require_role(request.user, MANAGER_ROLES)
        homework = self.get_object()
        if homework.status != 'draft' or homework.submissions.exists():
            raise ValidationError('Only empty draft homework can be deleted.')
        return super().destroy(request, *args, **kwargs)


class HomeworkActionAPIView(APIView):
    permission_classes = (IsActiveSchoolUser,)
    throttle_scope = 'homework_write'
    service_action = None

    @extend_schema(request=None, responses={200: HomeworkSerializer})
    def post(self, request, pk):
        _require_role(request.user, MANAGER_ROLES)
        homework = generics.get_object_or_404(homework_for_user(request.user, request), pk=pk)
        result = self.service_action(homework=homework, actor=request.user, request=request)
        return Response(HomeworkSerializer(result, context={'request': request}).data)


class PublishHomeworkAPIView(HomeworkActionAPIView):
    service_action = staticmethod(publish_homework)


class CloseHomeworkAPIView(HomeworkActionAPIView):
    service_action = staticmethod(close_homework)


class BulkHomeworkActionAPIView(APIView):
    permission_classes = (IsActiveSchoolUser,)
    throttle_scope = 'homework_write'
    service_action = None

    @extend_schema(request=BulkHomeworkSerializer, responses={200: HomeworkSerializer(many=True)})
    def post(self, request):
        _require_role(request.user, MANAGER_ROLES)
        payload = BulkHomeworkSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        ids = payload.validated_data['homework_ids']
        items = list(homework_for_user(request.user, request).filter(pk__in=ids).order_by('pk'))
        if len(items) != len(ids):
            raise NotFound('One or more homework records were not found.')
        saved = self.service_action(homework_items=items, actor=request.user, request=request)
        return Response(HomeworkSerializer(saved, many=True, context={'request': request}).data)


class BulkPublishHomeworkAPIView(BulkHomeworkActionAPIView):
    service_action = staticmethod(bulk_publish_homework)


class BulkCloseHomeworkAPIView(BulkHomeworkActionAPIView):
    service_action = staticmethod(bulk_close_homework)


class HomeworkSubmissionCreateAPIView(APIView):
    permission_classes = (IsActiveSchoolUser,)
    throttle_scope = 'homework_submit'

    @extend_schema(request=None, responses={200: HomeworkSubmissionSerializer})
    def post(self, request, pk):
        _require_role(request.user, ('student',))
        homework = generics.get_object_or_404(homework_for_user(request.user, request), pk=pk)
        enrollment = StudentEnrollment.objects.filter(
            student__user=request.user, is_current=True, status='active',
            academic_year_id=homework.academic_year_id,
            classroom_id=homework.teacher_assignment.classroom_id,
            section_id=homework.teacher_assignment.section_id,
        ).first()
        if not enrollment:
            raise NotFound('Homework was not found.')
        submission = create_submission_draft(
            homework=homework, student_enrollment=enrollment,
            actor=request.user, request=request,
        )
        return Response(
            HomeworkSubmissionSerializer(submission, context={'request': request}).data,
            status=status.HTTP_200_OK,
        )


class HomeworkSubmissionDetailAPIView(generics.RetrieveUpdateAPIView):
    serializer_class = HomeworkSubmissionSerializer
    permission_classes = (IsActiveSchoolUser,)
    throttle_scope = 'homework_submit'

    def get_queryset(self):
        return submissions_for_user(self.request.user, self.request)

    def update(self, request, *args, **kwargs):
        _require_role(request.user, ('student',))
        submission = self.get_object()
        payload = SubmissionAnswerSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        saved = update_submission_draft(
            submission=submission, actor=request.user, request=request,
            answer=payload.validated_data['answer'],
        )
        return Response(self.get_serializer(saved).data)


class FinalSubmitAPIView(APIView):
    permission_classes = (IsActiveSchoolUser,)
    throttle_scope = 'homework_submit'

    @extend_schema(request=None, responses={200: HomeworkSubmissionSerializer})
    def post(self, request, pk):
        _require_role(request.user, ('student',))
        submission = generics.get_object_or_404(submissions_for_user(request.user, request), pk=pk)
        saved = final_submit_homework(submission=submission, actor=request.user, request=request)
        return Response(HomeworkSubmissionSerializer(saved, context={'request': request}).data)


class ReturnSubmissionAPIView(APIView):
    permission_classes = (IsActiveSchoolUser,)
    throttle_scope = 'homework_write'

    @extend_schema(request=ReturnSubmissionSerializer, responses={200: HomeworkSubmissionSerializer})
    def post(self, request, pk):
        _require_role(request.user, MANAGER_ROLES)
        submission = generics.get_object_or_404(submissions_for_user(request.user, request), pk=pk)
        payload = ReturnSubmissionSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        saved = return_submission(
            submission=submission, actor=request.user, request=request,
            **payload.validated_data,
        )
        return Response(HomeworkSubmissionSerializer(saved, context={'request': request}).data)


class GradeSubmissionAPIView(APIView):
    permission_classes = (IsActiveSchoolUser,)
    throttle_scope = 'homework_write'

    @extend_schema(request=GradeSubmissionSerializer, responses={200: HomeworkSubmissionSerializer})
    def post(self, request, pk):
        _require_role(request.user, MANAGER_ROLES)
        submission = generics.get_object_or_404(submissions_for_user(request.user, request), pk=pk)
        payload = GradeSubmissionSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        saved = grade_submission(
            submission=submission, actor=request.user, request=request,
            **payload.validated_data,
        )
        return Response(HomeworkSubmissionSerializer(saved, context={'request': request}).data)


class BulkGradeSubmissionsAPIView(APIView):
    permission_classes = (IsActiveSchoolUser,)
    throttle_scope = 'homework_bulk_grade'

    @extend_schema(request=BulkGradeSubmissionsSerializer, responses={200: HomeworkSubmissionSerializer(many=True)})
    def post(self, request):
        _require_role(request.user, MANAGER_ROLES)
        payload = BulkGradeSubmissionsSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        submitted = payload.validated_data['items']
        ids = [item['submission_id'] for item in submitted]
        scoped = {item.pk: item for item in submissions_for_user(request.user, request).filter(pk__in=ids)}
        if len(scoped) != len(ids):
            raise NotFound('One or more submissions were not found.')
        items = []
        for item in submitted:
            values = dict(item)
            submission_id = values.pop('submission_id')
            values['submission'] = scoped[submission_id]
            items.append(values)
        saved = bulk_grade_submissions(items=items, actor=request.user, request=request)
        return Response(HomeworkSubmissionSerializer(saved, many=True, context={'request': request}).data)


class HomeworkSubmissionsAPIView(generics.ListAPIView):
    queryset = HomeworkSubmission.objects.none()
    serializer_class = HomeworkSubmissionSerializer
    permission_classes = (IsActiveSchoolUser,)

    @extend_schema(operation_id='homework_submissions_by_homework')
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        _require_role(self.request.user, MANAGER_ROLES)
        homework = generics.get_object_or_404(homework_for_user(self.request.user, self.request), pk=self.kwargs['pk'])
        return submissions_for_user(self.request.user, self.request).filter(homework=homework)


class SubmissionListAPIView(generics.ListAPIView):
    serializer_class = HomeworkSubmissionSerializer
    permission_classes = (IsActiveSchoolUser,)

    @extend_schema(
        operation_id='homework_submission_list',
        parameters=[SubmissionQuerySerializer],
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        query = SubmissionQuerySerializer(data=self.request.query_params)
        query.is_valid(raise_exception=True)
        params = query.validated_data
        queryset = submissions_for_user(self.request.user, self.request)
        mapping = {
            'homework_id': 'homework_id', 'status': 'status',
            'student_id': 'student_enrollment__student_id',
        }
        for parameter, field in mapping.items():
            if parameter in params:
                queryset = queryset.filter(**{field: params[parameter]})
        if params.get('submitted_from'):
            queryset = queryset.filter(submitted_at__gte=params['submitted_from'])
        if params.get('submitted_to'):
            queryset = queryset.filter(submitted_at__lte=params['submitted_to'])
        if params.get('graded') is not None:
            queryset = queryset.filter(grade__isnull=not params['graded'])
        if params.get('late') is not None:
            late_query = Q(submitted_at__gt=models_field('homework__due_date'))
            queryset = queryset.filter(late_query) if params['late'] else queryset.exclude(late_query)
        return queryset.order_by(params['ordering'])


def models_field(name):
    from django.db.models import F
    return F(name)


class AttachmentAPIView(APIView):
    permission_classes = (IsActiveSchoolUser,)
    parser_classes = (MultiPartParser, FormParser)
    throttle_scope = 'attachment_upload'
    kind = None

    def _parent(self, request, pk):
        if self.kind == 'homework':
            return generics.get_object_or_404(homework_for_user(request.user, request), pk=pk)
        return generics.get_object_or_404(submissions_for_user(request.user, request), pk=pk)

    @extend_schema(responses={200: HomeworkAttachmentSerializer(many=True)})
    def get(self, request, pk):
        parent = self._parent(request, pk)
        serializer = HomeworkAttachmentSerializer if self.kind == 'homework' else SubmissionAttachmentSerializer
        return Response(serializer(parent.attachments.all(), many=True, context={'request': request}).data)

    @extend_schema(request=AttachmentUploadSerializer, responses={201: HomeworkAttachmentSerializer(many=True)})
    def post(self, request, pk):
        parent = self._parent(request, pk)
        payload = AttachmentUploadSerializer(data={'files': request.FILES.getlist('files')})
        payload.is_valid(raise_exception=True)
        if self.kind == 'homework':
            _require_role(request.user, MANAGER_ROLES)
            created = add_homework_attachment(
                homework=parent, files=payload.validated_data['files'], actor=request.user, request=request,
            )
            serializer = HomeworkAttachmentSerializer
        else:
            _require_role(request.user, ('student',))
            created = add_submission_attachment(
                submission=parent, files=payload.validated_data['files'], actor=request.user, request=request,
            )
            serializer = SubmissionAttachmentSerializer
        return Response(serializer(created, many=True, context={'request': request}).data, status=status.HTTP_201_CREATED)


class HomeworkAttachmentAPIView(AttachmentAPIView):
    kind = 'homework'


class SubmissionAttachmentAPIView(AttachmentAPIView):
    kind = 'submission'


class AttachmentDeleteAPIView(APIView):
    permission_classes = (IsActiveSchoolUser,)
    kind = None

    @extend_schema(request=None, responses={204: None})
    def delete(self, request, pk, attachment_id):
        if self.kind == 'homework':
            parent = generics.get_object_or_404(homework_for_user(request.user, request), pk=pk)
            attachment = generics.get_object_or_404(
                HomeworkAttachment.objects.filter(homework=parent), pk=attachment_id,
            )
            delete_homework_attachment(attachment=attachment, actor=request.user, request=request)
        else:
            parent = generics.get_object_or_404(submissions_for_user(request.user, request), pk=pk)
            attachment = generics.get_object_or_404(
                HomeworkSubmissionAttachment.objects.filter(submission=parent), pk=attachment_id,
            )
            delete_submission_attachment(attachment=attachment, actor=request.user, request=request)
        return Response(status=status.HTTP_204_NO_CONTENT)


class HomeworkAttachmentDeleteAPIView(AttachmentDeleteAPIView):
    kind = 'homework'


class SubmissionAttachmentDeleteAPIView(AttachmentDeleteAPIView):
    kind = 'submission'


def _homework_summary(homework):
    target_students = StudentEnrollment.objects.filter(
        academic_year_id=homework.academic_year_id,
        classroom_id=homework.teacher_assignment.classroom_id,
        section_id=homework.teacher_assignment.section_id,
        is_current=True, status='active',
    ).count()
    stats = homework.submissions.aggregate(
        total=Count('id'),
        draft=Count('id', filter=Q(status='draft')),
        submitted=Count('id', filter=Q(status='submitted')),
        graded=Count('id', filter=Q(status='graded')),
        returned=Count('id', filter=Q(status='returned')),
        late=Count('id', filter=Q(submitted_at__gt=homework.due_date)),
        average_grade=Avg('grade'), highest_grade=Max('grade'), lowest_grade=Min('grade'),
    )
    submitted = stats['submitted'] + stats['graded'] + stats['returned']
    return {
        'homework_id': homework.pk, 'target_students': target_students,
        'submitted': stats['submitted'], 'not_started': max(target_students - (stats['total'] or 0), 0),
        'drafts': stats['draft'], 'graded': stats['graded'], 'returned': stats['returned'],
        'late': stats['late'], 'missing': max(target_students - submitted, 0),
        'completion_rate': round((submitted / target_students * 100), 2) if target_students else 0,
        'grading_progress': round((stats['graded'] / submitted * 100), 2) if submitted else 0,
        'pending_grading_count': stats['submitted'],
        'average_grade': stats['average_grade'], 'highest_grade': stats['highest_grade'],
        'lowest_grade': stats['lowest_grade'],
    }


class HomeworkSummaryAPIView(APIView):
    permission_classes = (IsActiveSchoolUser,)
    throttle_scope = 'reports'

    @extend_schema(responses={200: OpenApiTypes.OBJECT})
    def get(self, request, pk):
        _require_role(request.user, MANAGER_ROLES)
        homework = generics.get_object_or_404(homework_for_user(request.user, request), pk=pk)
        return Response(_homework_summary(homework))



def _filter_report_queryset(queryset, params):
    mapping = {
        'section_id': 'student_enrollment__section_id',
        'academic_year_id': 'homework__academic_year_id',
        'academic_term_id': 'homework__academic_term_id',
    }
    for parameter, field in mapping.items():
        if parameter in params:
            queryset = queryset.filter(**{field: params[parameter]})
    if params.get('date_from'):
        queryset = queryset.filter(homework__created_at__gte=params['date_from'])
    if params.get('date_to'):
        queryset = queryset.filter(homework__created_at__lte=params['date_to'])
    return queryset
class StudentHomeworkSummaryAPIView(APIView):
    permission_classes = (IsActiveSchoolUser,)
    throttle_scope = 'reports'

    @extend_schema(parameters=[HomeworkReportQuerySerializer], responses={200: OpenApiTypes.OBJECT})
    def get(self, request, student_id):
        student = generics.get_object_or_404(students_for_user(request.user), pk=student_id)
        query = HomeworkReportQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        params = query.validated_data
        queryset = submissions_for_user(request.user, request).filter(student_enrollment__student=student)
        queryset = _filter_report_queryset(queryset, params)
        return Response({'student_id': student.pk, 'statistics': queryset.aggregate(
            total=Count('id'), submitted=Count('id', filter=Q(status='submitted')),
            graded=Count('id', filter=Q(status='graded')),
            returned=Count('id', filter=Q(status='returned')),
            average_grade=Avg('grade'),
        )})


class ClassHomeworkSummaryAPIView(APIView):
    permission_classes = (IsActiveSchoolUser,)
    throttle_scope = 'reports'

    @extend_schema(parameters=[HomeworkReportQuerySerializer], responses={200: OpenApiTypes.OBJECT})
    def get(self, request, classroom_id):
        _require_role(request.user, MANAGER_ROLES)
        classroom = generics.get_object_or_404(
            Classroom.objects.filter(pk__in=homework_for_user(request.user, request).values('teacher_assignment__classroom_id')),
            pk=classroom_id,
        )
        query = HomeworkReportQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        params = query.validated_data
        queryset = submissions_for_user(request.user, request).filter(student_enrollment__classroom=classroom)
        queryset = _filter_report_queryset(queryset, params)
        return Response({'classroom_id': classroom.pk, 'statistics': queryset.aggregate(
            total=Count('id'), submitted=Count('id', filter=Q(status='submitted')),
            graded=Count('id', filter=Q(status='graded')),
            returned=Count('id', filter=Q(status='returned')),
            average_grade=Avg('grade'),
        )})


class StudentOwnHomeworkAPIView(HomeworkListCreateAPIView):
    http_method_names = ('get', 'head', 'options')

    def get_queryset(self):
        if self.request.user.role != 'student':
            raise PermissionDenied('Student access is required.')
        return super().get_queryset()


class ParentChildHomeworkAPIView(HomeworkListCreateAPIView):
    http_method_names = ('get', 'head', 'options')

    def get_queryset(self):
        _require_role(self.request.user, ('parent',))
        student = generics.get_object_or_404(students_for_user(self.request.user), pk=self.kwargs['student_id'])
        membership = getattr(self.request, 'active_membership', None)
        if membership is None:
            raise PermissionDenied('An active school context is required.')
        enrollments = student.enrollments.filter(school_id=membership.school_id)
        if membership.status == 'active':
            enrollments = enrollments.filter(is_current=True, status='active')
        scope = Q()
        for enrollment in enrollments:
            scope |= Q(
                academic_year_id=enrollment.academic_year_id,
                teacher_assignment__classroom_id=enrollment.classroom_id,
                teacher_assignment__section_id=enrollment.section_id,
            )
        return super().get_queryset().filter(scope) if scope else homework_for_user(self.request.user, self.request).none()


class TeacherOwnHomeworkAPIView(HomeworkListCreateAPIView):
    http_method_names = ('get', 'head', 'options')

    def get_queryset(self):
        if self.request.user.role != 'teacher':
            raise PermissionDenied('Teacher access is required.')
        return super().get_queryset()
class HomeworkDashboardAPIView(APIView):
    permission_classes = (IsActiveSchoolUser,)
    throttle_scope = 'homework_dashboard'

    @extend_schema(responses={200: OpenApiTypes.OBJECT})
    def get(self, request):
        role = request.active_role
        queryset = homework_for_user(request.user, request)
        now = timezone.now()
        if role == 'teacher':
            active = queryset.filter(status='published')
            pending = submissions_for_user(request.user, request).filter(status='submitted').count()
            return Response({
                'active_homework_count': active.count(), 'pending_grading_count': pending,
                'overdue_homework_count': active.filter(due_date__lt=now).count(),
                'recent_homework': HomeworkSerializer(queryset[:5], many=True, context={'request': request}).data,
                'homework_needing_action': HomeworkSerializer(active.filter(due_date__lt=now)[:5], many=True, context={'request': request}).data,
            })
        if role == 'student':
            rows = list(queryset)
            data = [HomeworkSerializer(item, context={'request': request}).data for item in rows]
            today = timezone.localdate()
            week = today + timedelta(days=7)
            return Response({
                'due_today_count': sum(item.due_date.date() == today for item in rows),
                'due_this_week_count': sum(today <= item.due_date.date() <= week for item in rows),
                'overdue_count': sum(item['completion_status'] == 'overdue' for item in data),
                'returned_count': sum(item['completion_status'] == 'returned' for item in data),
                'pending_grades_count': sum(item['completion_status'] == 'submitted' for item in data),
                'next_due_homework': next((item for item in data if item['completion_status'] not in ('graded', 'closed_without_submission')), None),
            })
        submissions = submissions_for_user(request.user, request)
        if role == 'parent':
            return Response({
                'children_summary': [],
                'missing_count': queryset.filter(due_date__lt=now).exclude(submissions__in=submissions).count(),
                'due_soon_count': queryset.filter(due_date__gte=now, due_date__lte=now + timedelta(days=7)).count(),
                'recently_graded_count': submissions.filter(status='graded', graded_at__gte=now-timedelta(days=7)).count(),
            })
        target = StudentEnrollment.objects.filter(
            school=request.active_school, is_current=True, status='active',
        ).count() * queryset.filter(status__in=('published', 'closed')).count()
        submitted = submissions.exclude(status='draft').count()
        return Response({
            'active_homework_count': queryset.filter(status='published').count(),
            'overall_completion_rate': round(submitted * 100 / target, 2) if target else 0,
            'pending_grading_count': submissions.filter(status='submitted').count(),
            'missing_submissions_count': max(target-submitted, 0),
        })