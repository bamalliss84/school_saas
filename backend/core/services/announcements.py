import logging
from functools import partial

from django.conf import settings
from django.db import transaction
from django.db.models import Q, Subquery
from django.utils import timezone
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError

from core.models import (
    Announcement, AnnouncementAttachment, AnnouncementReceipt, HomeworkActionLog,
    SchoolMembership, StudentEnrollment, StudentGuardian, TeacherAssignment,
)
from core.services.exam_results import request_audit_metadata
from core.services.homework import validate_attachment
from core.services.notifications import create_notifications_bulk

logger = logging.getLogger(__name__)


def _audit(*, announcement, membership, action, request=None, old_data=None, new_data=None):
    HomeworkActionLog.objects.create(
        school_id=announcement.school_id,
        actor_id=membership.user_id if membership else None,
        action=action,
        entity_type='announcement',
        entity_id=announcement.pk,
        old_data=old_data or {},
        new_data=new_data or {},
        **request_audit_metadata(request),
    )


def _require_active_context(membership):
    if membership is None or membership.status != 'active' or not membership.school.is_active:
        raise PermissionDenied('An active school context is required.')


def _can_manage(membership, announcement=None):
    _require_active_context(membership)
    if membership.role in ('super_admin', 'school_admin'):
        return True
    if membership.role != 'teacher':
        return False
    if announcement is None:
        return True
    return announcement.created_by_membership_id == membership.pk


def _validate_target(announcement, membership):
    announcement.full_clean(exclude=('target_students',))
    mode = announcement.audience_type
    if mode != 'roles' and announcement.target_roles:
        raise ValidationError('Target roles are allowed only for role targeting.')
    if mode not in ('classroom', 'section') and announcement.classroom_id:
        raise ValidationError('Classroom is not valid for this audience type.')
    if mode != 'section' and announcement.section_id:
        raise ValidationError('Section is not valid for this audience type.')
    if mode != 'teacher_assignment' and announcement.teacher_assignment_id:
        raise ValidationError('Teacher assignment is not valid for this audience type.')
    if mode in ('school', 'roles') and announcement.include_parents:
        raise ValidationError('Parent expansion is not valid for this audience type.')
    if membership.school_id != announcement.school_id:
        raise PermissionDenied('Announcement belongs to another school.')
    if membership.role == 'teacher':
        if announcement.audience_type != 'teacher_assignment':
            raise PermissionDenied('Teachers can target only their own assignment.')
        assignment = announcement.teacher_assignment
        if not assignment or not assignment.is_current:
            raise ValidationError('A current teacher assignment is required.')
        if assignment.teacher.user_id != membership.user_id:
            raise PermissionDenied('You cannot target another teacher assignment.')
        if announcement.academic_year_id and announcement.academic_year_id != assignment.academic_year_id:
            raise ValidationError('Academic year must match the teacher assignment.')


def _student_ids_for_announcement(announcement):
    enrollments = StudentEnrollment.objects.filter(
        school_id=announcement.school_id,
        is_current=True,
        status='active',
    )
    if announcement.academic_year_id:
        enrollments = enrollments.filter(academic_year_id=announcement.academic_year_id)
    if announcement.audience_type == 'classroom':
        enrollments = enrollments.filter(classroom_id=announcement.classroom_id)
    elif announcement.audience_type == 'section':
        enrollments = enrollments.filter(
            classroom_id=announcement.classroom_id,
            section_id=announcement.section_id,
        )
    elif announcement.audience_type == 'teacher_assignment':
        assignment = announcement.teacher_assignment
        enrollments = enrollments.filter(
            academic_year_id=assignment.academic_year_id,
            classroom_id=assignment.classroom_id,
            section_id=assignment.section_id,
        )
    elif announcement.audience_type == 'students':
        enrollments = enrollments.filter(student_id__in=announcement.target_students.values('pk'))
    return enrollments.values_list('student_id', flat=True)


def resolve_recipient_memberships(announcement):
    base = SchoolMembership.objects.filter(
        school_id=announcement.school_id,
        status='active',
        school__is_active=True,
    ).exclude(role='super_admin')
    if announcement.audience_type == 'school':
        return base
    if announcement.audience_type == 'roles':
        return base.filter(role__in=announcement.target_roles)

    student_ids = set(_student_ids_for_announcement(announcement))
    student_user_ids = set(StudentEnrollment.objects.filter(
        student_id__in=student_ids,
        school_id=announcement.school_id,
    ).exclude(student__user_id__isnull=True).values_list('student__user_id', flat=True))
    query = Q(role='student', user_id__in=student_user_ids)
    if announcement.include_parents:
        parent_user_ids = set(StudentGuardian.objects.filter(
            student_id__in=student_ids,
            can_receive_notifications=True,
            parent__user_id__isnull=False,
        ).values_list('parent__user_id', flat=True))
        query |= Q(role='parent', user_id__in=parent_user_ids)
    return base.filter(query)


@transaction.atomic
def create_announcement(*, membership, request=None, target_student_ids=(), **values):
    if not _can_manage(membership):
        raise PermissionDenied('You cannot create announcements.')
    announcement = Announcement(
        school=membership.school,
        created_by_membership=membership,
        **values,
    )
    _validate_target(announcement, membership)
    announcement.save()
    if target_student_ids and announcement.audience_type != 'students':
        raise ValidationError('Student targets are allowed only for student targeting.')
    if target_student_ids:
        students = announcement.target_students.model.objects.filter(
            pk__in=tuple(target_student_ids),
            school_id=announcement.school_id,
        )
        if students.count() != len(set(target_student_ids)):
            raise NotFound('One or more students were not found.')
        announcement.target_students.set(students)
    if announcement.audience_type == 'students' and not announcement.target_students.exists():
        raise ValidationError('At least one student is required.')
    _audit(
        announcement=announcement,
        membership=membership,
        action='announcement_create',
        request=request,
        new_data={'status': announcement.status, 'audience_type': announcement.audience_type},
    )
    return announcement


@transaction.atomic
def update_announcement(*, announcement, membership, request=None, target_student_ids=None, **changes):
    item = Announcement.objects.select_for_update(of=('self',)).select_related(
        'school', 'teacher_assignment__teacher', 'created_by_membership',
    ).get(pk=announcement.pk)
    if not _can_manage(membership, item):
        raise PermissionDenied('You cannot update this announcement.')
    if item.status != 'draft':
        raise ValidationError('Only draft announcements can be updated.')
    allowed = {
        'academic_year', 'title', 'body', 'priority', 'audience_type', 'target_roles',
        'classroom', 'section', 'teacher_assignment', 'include_parents', 'allow_inquiry',
    }
    if set(changes) - allowed:
        raise ValidationError('Unsupported announcement fields.')
    old = {'title': item.title, 'audience_type': item.audience_type, 'priority': item.priority}
    for field, value in changes.items():
        setattr(item, field, value)
    _validate_target(item, membership)
    item.save()
    if target_student_ids and item.audience_type != 'students':
        raise ValidationError('Student targets are allowed only for student targeting.')
    if target_student_ids is not None:
        students = item.target_students.model.objects.filter(
            pk__in=tuple(target_student_ids), school_id=item.school_id,
        )
        if students.count() != len(set(target_student_ids)):
            raise NotFound('One or more students were not found.')
        item.target_students.set(students)
    if item.audience_type != 'students':
        item.target_students.clear()
    if item.audience_type == 'students' and not item.target_students.exists():
        raise ValidationError('At least one student is required.')
    _audit(
        announcement=item, membership=membership, action='announcement_update', request=request,
        old_data=old,
        new_data={'title': item.title, 'audience_type': item.audience_type, 'priority': item.priority},
    )
    return item


def _notify_announcement_published_safely(announcement_id):
    try:
        announcement = Announcement.objects.get(pk=announcement_id)
        memberships = SchoolMembership.objects.filter(
            announcement_receipts__announcement_id=announcement_id,
            status='active', school_id=announcement.school_id,
        ).distinct()
        create_notifications_bulk(
            memberships=memberships,
            notification_type='announcement_published',
            title=announcement.title,
            body=announcement.body[:240],
            source_type='announcement',
            source_id=announcement.pk,
            payload={'action': {'route': 'announcement_detail', 'params': {'announcement_id': announcement.pk}}},
            deduplication_key_factory=lambda membership_id: (
                f'announcement:{announcement.pk}:published:{announcement.published_at.isoformat()}:'
                f'membership:{membership_id}'
            ),
        )
    except Exception:
        logger.exception('Announcement publication notification failed after commit.')


@transaction.atomic
def publish_announcement(*, announcement, membership, request=None):
    item = Announcement.objects.select_for_update(of=('self',)).select_related(
        'school', 'teacher_assignment__teacher', 'created_by_membership',
    ).prefetch_related('target_students').get(pk=announcement.pk)
    if not _can_manage(membership, item):
        raise PermissionDenied('You cannot publish this announcement.')
    if item.status != 'draft':
        raise ValidationError('Only draft announcements can be published.')
    _validate_target(item, membership)
    recipients = list(resolve_recipient_memberships(item).values_list('pk', flat=True))
    if not recipients:
        raise ValidationError('Announcement has no eligible recipients.')
    now = timezone.now()
    item.status = 'published'
    item.published_at = now
    item.published_by_membership = membership
    item.save(update_fields=('status', 'published_at', 'published_by_membership', 'updated_at'))
    AnnouncementReceipt.objects.bulk_create([
        AnnouncementReceipt(announcement=item, recipient_membership_id=membership_id)
        for membership_id in recipients
    ], ignore_conflicts=True)
    _audit(
        announcement=item, membership=membership, action='announcement_publish', request=request,
        old_data={'status': 'draft'},
        new_data={'status': 'published', 'recipient_count': len(recipients)},
    )
    transaction.on_commit(partial(_notify_announcement_published_safely, item.pk))
    return item


@transaction.atomic
def close_announcement(*, announcement, membership, request=None):
    item = Announcement.objects.select_for_update().get(pk=announcement.pk)
    if not _can_manage(membership, item):
        raise PermissionDenied('You cannot close this announcement.')
    if item.status != 'published':
        raise ValidationError('Only published announcements can be closed.')
    item.status = 'closed'
    item.closed_at = timezone.now()
    item.save(update_fields=('status', 'closed_at', 'updated_at'))
    _audit(
        announcement=item, membership=membership, action='announcement_close', request=request,
        old_data={'status': 'published'}, new_data={'status': 'closed'},
    )
    return item


@transaction.atomic
def archive_announcement(*, announcement, membership, request=None):
    item = Announcement.objects.select_for_update().get(pk=announcement.pk)
    if not _can_manage(membership, item):
        raise PermissionDenied('You cannot archive this announcement.')
    if item.status not in ('published', 'closed'):
        raise ValidationError('Only published or closed announcements can be archived.')
    old_status = item.status
    item.status = 'archived'
    item.archived_at = timezone.now()
    item.save(update_fields=('status', 'archived_at', 'updated_at'))
    _audit(
        announcement=item, membership=membership, action='announcement_archive', request=request,
        old_data={'status': old_status}, new_data={'status': 'archived'},
    )
    return item


@transaction.atomic
def mark_announcement_read(*, announcement, membership):
    receipt = AnnouncementReceipt.objects.select_for_update().filter(
        announcement=announcement,
        recipient_membership=membership,
    ).first()
    if receipt is None:
        raise NotFound('Announcement was not found.')
    if receipt.read_at is None:
        receipt.read_at = timezone.now()
        receipt.save(update_fields=('read_at',))
    return receipt


def announcements_for_context(membership):
    """Return announcements visible in one explicit school-membership context.

    Recipient visibility is driven by immutable ``AnnouncementReceipt`` rows.
    A scalar subquery is intentionally used instead of a reverse join so later
    pagination, ordering, and prefetching cannot widen or accidentally collapse
    the membership-scoped result set.
    """
    if membership is None:
        return Announcement.objects.none()

    delivered_announcement_ids = AnnouncementReceipt.objects.filter(
        recipient_membership_id=membership.pk,
    ).values('announcement_id')

    visibility = Q(pk__in=Subquery(delivered_announcement_ids))
    if membership.status == 'active' and membership.role in ('school_admin', 'super_admin'):
        visibility |= Q(school_id=membership.school_id)
    elif membership.status == 'active' and membership.role == 'teacher':
        visibility |= Q(created_by_membership_id=membership.pk)

    return Announcement.objects.filter(visibility).select_related(
        'school', 'academic_year', 'classroom', 'section',
        'teacher_assignment__subject', 'created_by_membership__user',
        'published_by_membership__user',
    ).prefetch_related('attachments')


def _delete_file_safely(storage, name):
    try:
        if name:
            storage.delete(name)
    except Exception:
        logger.exception('Announcement attachment storage deletion failed after commit.')


@transaction.atomic
def add_announcement_attachments(*, announcement, membership, files):
    item = Announcement.objects.select_for_update().get(pk=announcement.pk)
    if not _can_manage(membership, item):
        raise PermissionDenied('You cannot add announcement attachments.')
    if item.status != 'draft':
        raise ValidationError('Attachments can be added only to draft announcements.')
    files = list(files)
    limit = getattr(settings, 'MAX_ATTACHMENTS_PER_ANNOUNCEMENT', 10)
    if item.attachments.count() + len(files) > limit:
        raise ValidationError('Announcement attachment limit exceeded.')
    for uploaded_file in files:
        validate_attachment(uploaded_file, kind='announcement')
    created = []
    stored = []
    try:
        for uploaded_file in files:
            attachment = AnnouncementAttachment(
                announcement=item,
                original_name=uploaded_file.name,
                content_type=getattr(uploaded_file, 'content_type', '') or '',
                file_size=uploaded_file.size,
                uploaded_by_membership=membership,
            )
            attachment.file.save(uploaded_file.name, uploaded_file, save=False)
            stored.append((attachment.file.storage, attachment.file.name))
            attachment.save()
            created.append(attachment)
    except Exception:
        for storage, name in stored:
            _delete_file_safely(storage, name)
        raise
    return created


@transaction.atomic
def delete_announcement_attachment(*, attachment, membership):
    item = AnnouncementAttachment.objects.select_for_update().select_related('announcement').get(pk=attachment.pk)
    if not _can_manage(membership, item.announcement):
        raise PermissionDenied('You cannot delete this attachment.')
    if item.announcement.status != 'draft':
        raise ValidationError('Attachments can be deleted only from draft announcements.')
    storage, name = item.file.storage, item.file.name
    item.delete()
    transaction.on_commit(partial(_delete_file_safely, storage, name))
