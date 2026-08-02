import logging
from collections.abc import Iterable

from django.db import IntegrityError, transaction
from django.db.models import Count, Q
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from core.models import Notification, SchoolMembership

logger = logging.getLogger(__name__)
MAX_PAYLOAD_BYTES = 4096
BLOCKED_PAYLOAD_KEYS = {
    'token', 'access_token', 'refresh_token', 'authorization', 'password',
    'secret', 'storage_path', 'file_path',
}
MAX_PAYLOAD_DEPTH = 8


def _validate_payload_value(value, *, depth=0):
    if depth > MAX_PAYLOAD_DEPTH:
        raise ValidationError('Notification payload is too deeply nested.')
    if isinstance(value, dict):
        for key, nested in value.items():
            if not isinstance(key, str) or key.casefold() in BLOCKED_PAYLOAD_KEYS:
                raise ValidationError('Notification payload is invalid.')
            _validate_payload_value(nested, depth=depth + 1)
    elif isinstance(value, (list, tuple)):
        for nested in value:
            _validate_payload_value(nested, depth=depth + 1)
    elif value is not None and not isinstance(value, (str, int, float, bool)):
        raise ValidationError('Notification payload is not JSON serializable.')


def _safe_payload(payload):
    import json
    value = payload or {}
    if not isinstance(value, dict):
        raise ValidationError('Notification payload is invalid.')
    _validate_payload_value(value)
    try:
        encoded = json.dumps(value, ensure_ascii=False, allow_nan=False).encode('utf-8')
    except (TypeError, ValueError) as exc:
        raise ValidationError('Notification payload is not JSON serializable.') from exc
    if len(encoded) > MAX_PAYLOAD_BYTES:
        raise ValidationError('Notification payload is too large.')
    return value


def _validate_membership(membership):
    if membership.status != 'active' or not membership.school.is_active:
        raise ValidationError('Notification recipient is not available.')


@transaction.atomic
def create_notification(*, recipient_membership, notification_type, title, body='', action_url='', payload=None, source_type='', source_id=None, deduplication_key=''):
    membership = SchoolMembership.objects.select_for_update().select_related('school').get(pk=recipient_membership.pk)
    _validate_membership(membership)
    values = dict(
        school=membership.school, recipient=membership.user,
        recipient_membership=membership, notification_type=notification_type,
        title=title, body=body, action_url=action_url, payload=_safe_payload(payload),
        source_type=source_type, source_id=source_id, deduplication_key=deduplication_key,
    )
    if deduplication_key:
        item, _ = Notification.objects.get_or_create(
            recipient_membership=membership, deduplication_key=deduplication_key,
            defaults=values,
        )
        return item
    return Notification.objects.create(**values)


@transaction.atomic
def create_notifications_bulk(*, memberships: Iterable, notification_type, title, body='', action_url='', payload=None, source_type='', source_id=None, deduplication_key_factory=None):
    payload = _safe_payload(payload)
    ids = tuple(dict.fromkeys(item.pk if hasattr(item, 'pk') else int(item) for item in memberships))
    recipients = list(SchoolMembership.objects.filter(
        pk__in=ids, status='active', school__is_active=True,
    ).select_related('school'))
    rows = []
    for membership in recipients:
        key = deduplication_key_factory(membership.pk) if deduplication_key_factory else ''
        rows.append(Notification(
            school_id=membership.school_id, recipient_id=membership.user_id,
            recipient_membership_id=membership.pk, notification_type=notification_type,
            title=title, body=body, action_url=action_url, payload=payload,
            source_type=source_type, source_id=source_id, deduplication_key=key,
        ))
    return Notification.objects.bulk_create(rows, ignore_conflicts=bool(deduplication_key_factory))


def notifications_for_membership(membership):
    if membership is None:
        return Notification.objects.none()
    return Notification.objects.filter(recipient_membership=membership).select_related('school', 'recipient_membership')


@transaction.atomic
def mark_notification_read(*, notification):
    item = Notification.objects.select_for_update().get(pk=notification.pk)
    if not item.is_read:
        item.is_read = True
        item.read_at = timezone.now()
        item.save(update_fields=('is_read', 'read_at', 'updated_at'))
    return item


def mark_all_notifications_read(*, membership):
    return Notification.objects.filter(
        recipient_membership=membership, is_read=False,
    ).update(is_read=True, read_at=timezone.now(), updated_at=timezone.now())


def get_unread_notification_count(membership):
    return Notification.objects.filter(recipient_membership=membership, is_read=False).count()


def get_context_unread_counts(memberships):
    ids = [item.pk for item in memberships]
    return dict(Notification.objects.filter(
        recipient_membership_id__in=ids, is_read=False,
    ).values_list('recipient_membership_id').annotate(total=Count('id')))


def run_notification_callback(callback, **safe_ids):
    try:
        callback(**safe_ids)
    except Exception:
        logger.exception('Post-commit notification integration failed.')

def _memberships_for_users(*, school_id, role_user_ids):
    query = Q()
    for role, user_ids in role_user_ids.items():
        if user_ids:
            query |= Q(role=role, user_id__in=user_ids)
    if not query:
        return SchoolMembership.objects.none()
    return SchoolMembership.objects.filter(
        query, school_id=school_id, status='active', school__is_active=True,
    ).select_related('school')


def _student_parent_memberships(enrollments):
    from core.models import StudentGuardian
    enrollments = list(enrollments)
    if not enrollments:
        return SchoolMembership.objects.none()
    school_id = enrollments[0].school_id
    student_user_ids = {row.student.user_id for row in enrollments if row.student.user_id}
    parent_user_ids = set(StudentGuardian.objects.filter(
        student_id__in={row.student_id for row in enrollments}, can_receive_notifications=True,
        parent__user__isnull=False,
    ).values_list('parent__user_id', flat=True))
    return _memberships_for_users(
        school_id=school_id, role_user_ids={'student': student_user_ids, 'parent': parent_user_ids},
    )


def notify_homework_published(*, homework_id):
    from core.models import Homework, HomeworkActionLog, StudentEnrollment
    homework = Homework.objects.select_related('teacher_assignment').get(pk=homework_id)
    event_id = HomeworkActionLog.objects.filter(
        school_id=homework.school_id, entity_type='homework', entity_id=homework_id, action='publish',
    ).order_by('-pk').values_list('pk', flat=True).first()
    enrollments = StudentEnrollment.objects.filter(
        school_id=homework.school_id, academic_year_id=homework.academic_year_id,
        classroom_id=homework.teacher_assignment.classroom_id,
        section_id=homework.teacher_assignment.section_id, is_current=True, status='active',
    ).select_related('student')
    memberships = _student_parent_memberships(enrollments)
    return create_notifications_bulk(
        memberships=memberships, notification_type='homework_published',
        title='New homework', body=homework.title[:200], source_type='homework', source_id=homework.pk,
        payload={'action': {'route': 'homework_detail', 'params': {'homework_id': homework.pk}}},
        deduplication_key_factory=lambda membership_id: f'homework:{homework.pk}:published:event:{event_id}:membership:{membership_id}',
    )


def _notify_submission(*, submission_id, kind):
    from core.models import HomeworkActionLog, HomeworkSubmission
    submission = HomeworkSubmission.objects.select_related('homework', 'student_enrollment__student').get(pk=submission_id)
    event_id = HomeworkActionLog.objects.filter(
        school_id=submission.homework.school_id, entity_type='submission', entity_id=submission_id,
        action='grade' if kind == 'homework_graded' else 'return',
    ).order_by('-pk').values_list('pk', flat=True).first()
    memberships = _student_parent_memberships([submission.student_enrollment])
    action = {'route': 'homework_submission', 'params': {'submission_id': submission.pk}}
    return create_notifications_bulk(
        memberships=memberships, notification_type=kind,
        title='Homework graded' if kind == 'homework_graded' else 'Homework returned',
        body=submission.homework.title[:200], source_type='homework_submission', source_id=submission.pk,
        payload={'action': action}, deduplication_key_factory=lambda membership_id: f'submission:{submission.pk}:{"graded" if kind == "homework_graded" else "returned"}:event:{event_id}:membership:{membership_id}',
    )


def notify_homework_graded(*, submission_id):
    return _notify_submission(submission_id=submission_id, kind='homework_graded')


def notify_homework_returned(*, submission_id):
    return _notify_submission(submission_id=submission_id, kind='homework_returned')


def notify_results_published(*, exam_id, result_ids):
    from core.models import ExamResult, ExamResultLog
    rows = ExamResult.objects.filter(
        pk__in=tuple(result_ids), exam_id=exam_id, workflow_status='approved', is_published=True,
    ).select_related('student_enrollment__student', 'exam')
    created = []
    for result in rows:
        event_id = ExamResultLog.objects.filter(exam_result=result, action='publish').order_by('-pk').values_list('pk', flat=True).first()
        memberships = _student_parent_memberships([result.student_enrollment])
        created.extend(create_notifications_bulk(
            memberships=memberships, notification_type='result_published', title='Result published',
            body=result.exam.title[:200], source_type='exam_result', source_id=result.pk,
            payload={'action': {'route': 'result_detail', 'params': {'result_id': result.pk}}},
            deduplication_key_factory=lambda membership_id, result=result, event_id=event_id: f'result:{result.pk}:published:event:{event_id}:membership:{membership_id}',
        ))
    return created