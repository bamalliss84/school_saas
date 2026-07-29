from django.db import transaction
from rest_framework.exceptions import PermissionDenied, ValidationError

from core.models import ExamResult, ExamResultLog
from core.selectors import user_can_manage_teacher_assignment


def request_audit_metadata(request):
    if request is None:
        return {'request_id': None, 'ip_address': None, 'user_agent': None}
    request_id = request.headers.get('X-Request-ID') or getattr(request, 'request_id', None)
    forwarded = request.META.get('HTTP_X_FORWARDED_FOR', '')
    ip_address = forwarded.split(',')[0].strip() if forwarded else request.META.get('REMOTE_ADDR')
    return {
        'request_id': request_id,
        'ip_address': ip_address or None,
        'user_agent': request.META.get('HTTP_USER_AGENT', '')[:512] or None,
    }


def _can_edit(user, exam_result):
    return user_can_manage_teacher_assignment(user, exam_result.exam.teacher_assignment)


def _is_approver(user, exam_result):
    if user.role == 'super_admin':
        return True
    return bool(
        user.role == 'school_admin'
        and user.school_id == exam_result.exam.school_id
    )


def _audit(*, result, old, changed_by, action, reason, request):
    ExamResultLog.objects.create(
        exam_result=result,
        old_score=old.get('score'),
        new_score=result.score,
        old_status=old.get('status'),
        new_status=result.status,
        old_workflow_status=old.get('workflow_status'),
        new_workflow_status=result.workflow_status,
        old_approval_reason=old.get('approval_reason'),
        new_approval_reason=result.approval_reason,
        changed_by=changed_by,
        action=action,
        reason=reason or None,
        **request_audit_metadata(request),
    )


@transaction.atomic
def create_exam_result(*, exam, student_enrollment, changed_by, request=None, **values):
    if not user_can_manage_teacher_assignment(changed_by, exam.teacher_assignment):
        raise PermissionDenied('You cannot manage this exam.')
    result = ExamResult(
        exam=exam,
        student_enrollment=student_enrollment,
        graded_by=changed_by,
        **values,
    )
    result.save()
    _audit(
        result=result,
        old={},
        changed_by=changed_by,
        action='create',
        reason='Result created.',
        request=request,
    )
    return result


@transaction.atomic
def update_exam_result(
    *, exam_result, changed_by, reason=None, action='update', request=None, **changes
):
    """Update a result through one audited, row-locked service."""
    if not isinstance(exam_result, ExamResult):
        raise TypeError('exam_result must be an ExamResult instance.')
    result = ExamResult.objects.select_for_update().select_related(
        'exam__teacher_assignment__teacher', 'exam__school',
    ).get(pk=exam_result.pk)
    if not _can_edit(changed_by, result):
        raise PermissionDenied('You cannot manage this result.')

    allowed_fields = {
        'score', 'status', 'remarks', 'graded_by', 'approved_by',
        'workflow_status', 'approval_reason',
    }
    unknown_fields = set(changes) - allowed_fields
    if unknown_fields:
        raise ValueError(f'Unsupported fields: {sorted(unknown_fields)}')
    if action == 'update' and result.workflow_status != 'draft':
        raise ValidationError('Only draft results can be edited.')

    old = {
        'score': result.score,
        'status': result.status,
        'workflow_status': result.workflow_status,
        'approval_reason': result.approval_reason,
    }
    for field, value in changes.items():
        setattr(result, field, value)
    if action == 'update':
        result.graded_by = changed_by
    result.save()
    changed = any((
        old['score'] != result.score,
        old['status'] != result.status,
        old['workflow_status'] != result.workflow_status,
        old['approval_reason'] != result.approval_reason,
    ))
    if changed:
        _audit(
            result=result,
            old=old,
            changed_by=changed_by,
            action=action,
            reason=reason or 'Result updated.',
            request=request,
        )
    return result


@transaction.atomic
def delete_exam_result(*, exam_result, changed_by):
    result = ExamResult.objects.select_for_update().select_related(
        'exam__teacher_assignment__teacher', 'exam__school',
    ).get(pk=exam_result.pk)
    if not _can_edit(changed_by, result):
        raise PermissionDenied('You cannot delete this result.')
    if result.workflow_status != 'draft':
        raise ValidationError('Only draft results can be deleted.')
    result.delete()


@transaction.atomic
def submit_exam_result(*, exam_result, changed_by, request=None):
    result = ExamResult.objects.select_for_update().select_related(
        'exam__teacher_assignment__teacher', 'exam__school',
    ).get(pk=exam_result.pk)
    if not _can_edit(changed_by, result):
        raise PermissionDenied('You cannot submit this result.')
    if result.workflow_status != 'draft':
        raise ValidationError('Only draft results can be submitted.')
    if result.status == 'not_graded':
        raise ValidationError('A result must be graded before submission.')
    return update_exam_result(
        exam_result=result,
        changed_by=changed_by,
        action='submit',
        request=request,
        workflow_status='submitted',
        approval_reason=None,
    )


@transaction.atomic
def approve_exam_result(*, exam_result, changed_by, reason=None, request=None):
    result = ExamResult.objects.select_for_update().select_related(
        'exam__teacher_assignment__teacher', 'exam__school',
    ).get(pk=exam_result.pk)
    if not _is_approver(changed_by, result):
        raise PermissionDenied('You cannot approve this result.')
    if result.workflow_status != 'submitted':
        raise ValidationError('Only submitted results can be approved.')
    return update_exam_result(
        exam_result=result,
        changed_by=changed_by,
        action='approve',
        reason=reason,
        request=request,
        workflow_status='approved',
        approval_reason=reason,
        approved_by=changed_by,
    )


@transaction.atomic
def reject_exam_result(*, exam_result, changed_by, reason, request=None):
    result = ExamResult.objects.select_for_update().select_related(
        'exam__teacher_assignment__teacher', 'exam__school',
    ).get(pk=exam_result.pk)
    if not _is_approver(changed_by, result):
        raise PermissionDenied('You cannot reject this result.')
    if result.workflow_status != 'submitted':
        raise ValidationError('Only submitted results can be rejected.')
    if not reason:
        raise ValidationError('A rejection reason is required.')
    return update_exam_result(
        exam_result=result,
        changed_by=changed_by,
        action='reject',
        reason=reason,
        request=request,
        workflow_status='draft',
        approval_reason=reason,
        approved_by=None,
    )


@transaction.atomic
def reopen_exam_result(*, exam_result, changed_by, reason=None, request=None):
    result = ExamResult.objects.select_for_update().select_related(
        'exam__teacher_assignment__teacher', 'exam__school',
    ).get(pk=exam_result.pk)
    if not _is_approver(changed_by, result):
        raise PermissionDenied('You cannot reopen this result.')
    if result.workflow_status != 'approved':
        raise ValidationError('Only approved results can be reopened.')
    return update_exam_result(
        exam_result=result,
        changed_by=changed_by,
        action='reopen',
        reason=reason,
        request=request,
        workflow_status='draft',
        approval_reason=reason,
        approved_by=None,
    )
