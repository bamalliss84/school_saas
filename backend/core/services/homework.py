import logging
import mimetypes
import os
from functools import partial
from pathlib import PurePath

from django.conf import settings
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, ValidationError

from core.models import (
    Homework, HomeworkActionLog, HomeworkAttachment, HomeworkSubmission,
    HomeworkSubmissionAttachment,
)
from core.selectors import user_can_manage_teacher_assignment
from core.services.exam_results import request_audit_metadata

logger = logging.getLogger(__name__)

BLOCKED_EXTENSIONS = {
    'exe', 'dll', 'bat', 'cmd', 'com', 'msi', 'ps1', 'sh', 'js', 'jar',
    'apk', 'dmg', 'iso', 'php', 'py', 'html', 'htm',
}


def homework_published_hook(*, homework_id):
    from .notifications import notify_homework_published
    return notify_homework_published(homework_id=homework_id)


def submission_graded_hook(*, submission_id):
    from .notifications import notify_homework_graded
    return notify_homework_graded(submission_id=submission_id)


def submission_returned_hook(*, submission_id):
    from .notifications import notify_homework_returned
    return notify_homework_returned(submission_id=submission_id)


def antivirus_scan_hook(*, uploaded_file):
    return None


def _safe_hook(hook, *, entity_id, keyword):
    try:
        hook(**{keyword: entity_id})
    except Exception:
        logger.exception('Homework post-commit hook failed.')


def _audit(*, school_id, actor, action, entity_type, entity_id, request=None,
           old_data=None, new_data=None, reason=''):
    HomeworkActionLog.objects.create(
        school_id=school_id,
        actor=actor,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        old_data=old_data or {},
        new_data=new_data or {},
        reason=reason or '',
        **request_audit_metadata(request),
    )


def _can_administer_school(user, school_id):
    return user.role == 'super_admin' or (
        user.role == 'school_admin' and user.school_id == school_id
    )


def _can_manage_homework(user, homework, request=None):
    return user_can_manage_teacher_assignment(user, homework.teacher_assignment, request=request)


def _validate_homework_relationships(homework):
    assignment = homework.teacher_assignment
    if (
        assignment.school_id != homework.school_id
        or assignment.academic_year_id != homework.academic_year_id
        or homework.academic_term.school_id != homework.school_id
        or homework.academic_term.academic_year_id != homework.academic_year_id
        or not assignment.is_current
    ):
        raise ValidationError('Invalid homework relationships.')


@transaction.atomic
def create_homework(*, actor, request=None, **values):
    assignment = values['teacher_assignment']
    if not user_can_manage_teacher_assignment(actor, assignment):
        raise PermissionDenied('You cannot create homework for this assignment.')
    if actor.role == 'teacher' and actor.academic_year_id != assignment.academic_year_id:
        raise PermissionDenied('You cannot create homework outside your academic year.')
    homework = Homework(created_by=actor, school=assignment.school, **values)
    _validate_homework_relationships(homework)
    homework.save()
    _audit(
        school_id=homework.school_id, actor=actor, action='create',
        entity_type='homework', entity_id=homework.pk, request=request,
        new_data={'status': homework.status, 'title': homework.title},
    )
    return homework


@transaction.atomic
def update_homework(*, homework, actor, request=None, **changes):
    item = Homework.objects.select_for_update().select_related(
        'teacher_assignment__teacher', 'academic_term', 'school',
    ).get(pk=homework.pk)
    if not _can_manage_homework(actor, item):
        raise PermissionDenied('You cannot update this homework.')
    if item.status != 'draft':
        raise ValidationError('Only draft homework can be updated.')
    old = {'status': item.status, 'title': item.title, 'due_date': item.due_date.isoformat()}
    allowed = {
        'academic_year', 'academic_term', 'teacher_assignment', 'title',
        'description', 'submission_type', 'publish_at', 'due_date', 'max_grade',
    }
    if set(changes) - allowed:
        raise ValidationError('Unsupported homework fields.')
    for field, value in changes.items():
        setattr(item, field, value)
    item.school = item.teacher_assignment.school
    _validate_homework_relationships(item)
    item.save()
    _audit(
        school_id=item.school_id, actor=actor, action='update',
        entity_type='homework', entity_id=item.pk, request=request,
        old_data=old,
        new_data={'status': item.status, 'title': item.title, 'due_date': item.due_date.isoformat()},
    )
    return item


@transaction.atomic
def publish_homework(*, homework, actor, request=None):
    item = Homework.objects.select_for_update().select_related(
        'teacher_assignment__teacher', 'academic_term', 'school',
    ).get(pk=homework.pk)
    if not _can_manage_homework(actor, item):
        raise PermissionDenied('You cannot publish this homework.')
    if item.status != 'draft':
        raise ValidationError('Only draft homework can be published.')
    _validate_homework_relationships(item)
    published_at = timezone.now()
    if item.due_date < published_at:
        raise ValidationError('Due date cannot precede publication time.')
    item.status = 'published'
    item.published_at = published_at
    item.save(update_fields=('status', 'published_at', 'updated_at'))
    _audit(
        school_id=item.school_id, actor=actor, action='publish',
        entity_type='homework', entity_id=item.pk, request=request,
        old_data={'status': 'draft'}, new_data={'status': 'published'},
    )
    transaction.on_commit(partial(
        _safe_hook, homework_published_hook,
        entity_id=item.pk, keyword='homework_id',
    ))
    return item


@transaction.atomic
def close_homework(*, homework, actor, request=None):
    item = Homework.objects.select_for_update().select_related(
        'teacher_assignment__teacher', 'school',
    ).get(pk=homework.pk)
    if not _can_manage_homework(actor, item):
        raise PermissionDenied('You cannot close this homework.')
    if item.status != 'published':
        raise ValidationError('Only published homework can be closed.')
    item.status = 'closed'
    item.save(update_fields=('status', 'updated_at'))
    _audit(
        school_id=item.school_id, actor=actor, action='close',
        entity_type='homework', entity_id=item.pk, request=request,
        old_data={'status': 'published'}, new_data={'status': 'closed'},
    )
    return item


@transaction.atomic
def bulk_publish_homework(*, homework_items, actor, request=None):
    return [publish_homework(homework=item, actor=actor, request=request) for item in homework_items]


@transaction.atomic
def bulk_close_homework(*, homework_items, actor, request=None):
    return [close_homework(homework=item, actor=actor, request=request) for item in homework_items]


def _validate_enrollment(homework, enrollment):
    assignment = homework.teacher_assignment
    if (
        not enrollment.is_current or enrollment.status != 'active'
        or enrollment.school_id != homework.school_id
        or enrollment.academic_year_id != homework.academic_year_id
        or enrollment.classroom_id != assignment.classroom_id
        or enrollment.section_id != assignment.section_id
    ):
        raise ValidationError('Student enrollment is outside this homework scope.')


def _student_owns(user, enrollment):
    return user.role == 'student' and enrollment.student.user_id == user.id


@transaction.atomic
def create_submission_draft(*, homework, student_enrollment, actor, request=None):
    item = Homework.objects.select_for_update().select_related('teacher_assignment').get(pk=homework.pk)
    if not _student_owns(actor, student_enrollment):
        raise PermissionDenied('You cannot create this submission.')
    if item.status != 'published':
        raise ValidationError('Homework is not accepting submissions.')
    if item.submission_type == 'none':
        raise ValidationError('This homework does not require an electronic submission.')
    _validate_enrollment(item, student_enrollment)
    submission, created = HomeworkSubmission.objects.select_for_update().get_or_create(
        homework=item, student_enrollment=student_enrollment,
    )
    if created:
        _audit(
            school_id=item.school_id, actor=actor, action='create',
            entity_type='submission', entity_id=submission.pk, request=request,
            new_data={'status': 'draft'},
        )
    return submission


@transaction.atomic
def update_submission_draft(*, submission, actor, answer, request=None):
    item = HomeworkSubmission.objects.select_for_update().select_related(
        'homework', 'student_enrollment__student',
    ).get(pk=submission.pk)
    if not _student_owns(actor, item.student_enrollment):
        raise PermissionDenied('You cannot update this submission.')
    if item.homework.status != 'published' or item.status not in ('draft', 'returned'):
        raise ValidationError('Submission cannot be edited.')
    if item.homework.submission_type == 'none':
        raise ValidationError('This homework does not require an electronic submission.')
    if item.homework.submission_type == 'attachment' and answer.strip():
        raise ValidationError({'answer': 'This homework accepts attachments only.'})
    old_status = item.status
    item.answer = answer
    item.save(update_fields=('answer', 'updated_at'))
    _audit(
        school_id=item.homework.school_id, actor=actor, action='update',
        entity_type='submission', entity_id=item.pk, request=request,
        old_data={'status': old_status}, new_data={'status': item.status, 'answer_changed': True},
    )
    return item


@transaction.atomic
def final_submit_homework(*, submission, actor, request=None):
    item = HomeworkSubmission.objects.select_for_update().select_related(
        'homework', 'student_enrollment__student',
    ).get(pk=submission.pk)
    if not _student_owns(actor, item.student_enrollment):
        raise PermissionDenied('You cannot submit this homework.')
    if item.homework.status != 'published' or item.status not in ('draft', 'returned'):
        raise ValidationError('Submission cannot be submitted.')
    submission_type = item.homework.submission_type
    if submission_type == 'none':
        raise ValidationError('This homework does not require an electronic submission.')
    has_text = bool(item.answer.strip())
    has_attachment = item.attachments.exists()
    if submission_type == 'text' and not has_text:
        raise ValidationError({'answer': 'A text answer is required.'})
    if submission_type == 'attachment' and not has_attachment:
        raise ValidationError({'attachments': 'At least one attachment is required.'})
    if submission_type == 'text_and_attachment':
        errors = {}
        if not has_text:
            errors['answer'] = 'A text answer is required.'
        if not has_attachment:
            errors['attachments'] = 'At least one attachment is required.'
        if errors:
            raise ValidationError(errors)
    old_status = item.status
    item.status = 'submitted'
    item.submitted_at = timezone.now()
    item.returned_at = None
    item.save(update_fields=('status', 'submitted_at', 'returned_at', 'updated_at'))
    _audit(
        school_id=item.homework.school_id, actor=actor, action='final_submit',
        entity_type='submission', entity_id=item.pk, request=request,
        old_data={'status': old_status}, new_data={'status': 'submitted'},
    )
    return item


@transaction.atomic
def return_submission(*, submission, actor, teacher_note='', request=None):
    item = HomeworkSubmission.objects.select_for_update().select_related(
        'homework__teacher_assignment__teacher',
    ).get(pk=submission.pk)
    if not _can_manage_homework(actor, item.homework, request=request):
        raise PermissionDenied('You cannot return this submission.')
    if item.status not in ('submitted', 'graded', 'reviewed'):
        raise ValidationError('Only submitted, graded, or reviewed work can be returned.')
    old_status = item.status
    item.status = 'returned'
    item.teacher_note = teacher_note
    item.grade = None
    item.graded_by = None
    item.graded_at = None
    item.returned_at = timezone.now()
    item.save()
    _audit(
        school_id=item.homework.school_id, actor=actor, action='return',
        entity_type='submission', entity_id=item.pk, request=request,
        old_data={'status': old_status}, new_data={'status': 'returned'},
    )
    transaction.on_commit(partial(
        _safe_hook, submission_returned_hook,
        entity_id=item.pk, keyword='submission_id',
    ))
    return item


@transaction.atomic
def review_submission(*, submission, actor, teacher_note='', request=None):
    item = HomeworkSubmission.objects.select_for_update().select_related(
        'homework__teacher_assignment__teacher',
    ).get(pk=submission.pk)
    if not _can_manage_homework(actor, item.homework, request=request):
        raise PermissionDenied('You cannot review this submission.')
    if item.status != 'submitted':
        raise ValidationError('Only submitted work can be reviewed.')
    if item.homework.max_grade is not None:
        raise ValidationError('This homework is graded. Use the grade action instead.')
    old_status = item.status
    item.status = 'reviewed'
    item.grade = None
    item.teacher_note = teacher_note
    item.graded_by = actor
    item.graded_at = timezone.now()
    item.save()
    _audit(
        school_id=item.homework.school_id, actor=actor, action='review',
        entity_type='submission', entity_id=item.pk, request=request,
        old_data={'status': old_status},
        new_data={'status': 'reviewed'},
    )
    return item


@transaction.atomic
def grade_submission(*, submission, actor, grade, teacher_note='', request=None):
    item = HomeworkSubmission.objects.select_for_update().select_related(
        'homework__teacher_assignment__teacher',
    ).get(pk=submission.pk)
    if not _can_manage_homework(actor, item.homework, request=request):
        raise PermissionDenied('You cannot grade this submission.')
    if item.status != 'submitted':
        raise ValidationError('Only submitted work can be graded.')
    if item.homework.max_grade is None:
        raise ValidationError('This homework is not graded.')
    if grade < 0 or grade > item.homework.max_grade:
        raise ValidationError('Grade is outside the allowed range.')
    item.status = 'graded'
    item.grade = grade
    item.teacher_note = teacher_note
    item.graded_by = actor
    item.graded_at = timezone.now()
    item.save()
    _audit(
        school_id=item.homework.school_id, actor=actor, action='grade',
        entity_type='submission', entity_id=item.pk, request=request,
        old_data={'status': 'submitted'},
        new_data={'status': 'graded', 'grade': str(grade)},
    )
    transaction.on_commit(partial(
        _safe_hook, submission_graded_hook,
        entity_id=item.pk, keyword='submission_id',
    ))
    return item


@transaction.atomic
def bulk_grade_submissions(*, items, actor, request=None):
    return [grade_submission(
        submission=item['submission'], actor=actor, grade=item['grade'],
        teacher_note=item.get('teacher_note', ''), request=request,
    ) for item in items]


def _setting(name, default):
    return getattr(settings, name, default)


def _normalized_name(uploaded_file):
    name = PurePath(str(uploaded_file.name).replace('\\', '/')).name
    if not name or name in ('.', '..') or len(name) > 255:
        raise ValidationError('Invalid attachment name.')
    return name


def validate_attachment(uploaded_file, *, kind):
    name = _normalized_name(uploaded_file)
    if uploaded_file.size <= 0:
        raise ValidationError('Attachment cannot be empty.')
    size_setting = {
        'homework': 'MAX_HOMEWORK_ATTACHMENT_SIZE_MB',
        'submission': 'MAX_SUBMISSION_ATTACHMENT_SIZE_MB',
        'message': 'MAX_MESSAGE_ATTACHMENT_SIZE_MB',
        'announcement': 'MAX_ANNOUNCEMENT_ATTACHMENT_SIZE_MB',
    }.get(kind, 'MAX_SUBMISSION_ATTACHMENT_SIZE_MB')
    limit = _setting(size_setting, 10) * 1024 * 1024
    if uploaded_file.size > limit:
        raise ValidationError('Attachment exceeds the allowed size.')
    suffixes = [suffix.lower().lstrip('.') for suffix in PurePath(name).suffixes]
    extension = suffixes[-1] if suffixes else ''
    allowed_extensions_setting = {
        'message': 'ALLOWED_MESSAGE_ATTACHMENT_EXTENSIONS',
        'announcement': 'ALLOWED_ANNOUNCEMENT_ATTACHMENT_EXTENSIONS',
    }.get(kind, 'ALLOWED_ATTACHMENT_EXTENSIONS')
    allowed_extensions = set(_setting(allowed_extensions_setting, ()))
    if not extension or any(suffix in BLOCKED_EXTENSIONS for suffix in suffixes):
        raise ValidationError('Attachment type is not allowed.')
    if allowed_extensions and extension not in allowed_extensions:
        raise ValidationError('Attachment type is not allowed.')
    declared = (getattr(uploaded_file, 'content_type', '') or '').lower()
    allowed_mimes_setting = {
        'message': 'ALLOWED_MESSAGE_ATTACHMENT_MIME_TYPES',
        'announcement': 'ALLOWED_ANNOUNCEMENT_ATTACHMENT_MIME_TYPES',
    }.get(kind, 'ALLOWED_ATTACHMENT_MIME_TYPES')
    allowed_mimes = set(_setting(allowed_mimes_setting, ()))
    guessed = (mimetypes.guess_type(name)[0] or '').lower()
    if not declared or declared not in allowed_mimes or guessed != declared:
        raise ValidationError('Attachment content type is not allowed.')
    position = uploaded_file.tell() if hasattr(uploaded_file, 'tell') else 0
    header = uploaded_file.read(8)
    if hasattr(uploaded_file, 'seek'):
        uploaded_file.seek(position)
    signatures = {
        'application/pdf': (b'%PDF-',),
        'image/jpeg': (b'\\xff\\xd8\\xff',),
        'image/png': (b'\\x89PNG\\r\\n\\x1a\\n',),
    }
    if declared in signatures and not any(header.startswith(value) for value in signatures[declared]):
        raise ValidationError('Attachment content does not match its declared type.')
    antivirus_scan_hook(uploaded_file=uploaded_file)
    return {'original_name': name, 'content_type': declared, 'file_size': uploaded_file.size}


def _add_attachments(*, parent, files, actor, model, relation_name, kind, max_count, request):
    if not files:
        raise ValidationError('At least one attachment is required.')
    existing = parent.attachments.count()
    if existing + len(files) > max_count:
        raise ValidationError('Attachment count exceeds the allowed limit.')
    metadata = [validate_attachment(file, kind=kind) for file in files]
    created = []
    try:
        with transaction.atomic():
            for uploaded_file, values in zip(files, metadata):
                attachment = model(uploaded_by=actor, file=uploaded_file, **values)
                setattr(attachment, relation_name, parent)
                attachment.save()
                created.append(attachment)
            _audit(
                school_id=(parent.school_id if kind == 'homework' else parent.homework.school_id),
                actor=actor, action='attachment_add', entity_type=kind,
                entity_id=parent.pk, request=request,
                new_data={'attachment_count': len(created)},
            )
    except Exception:
        for attachment in created:
            try:
                attachment.file.storage.delete(attachment.file.name)
            except Exception:
                logger.exception('Failed to clean attachment after rollback.')
        raise
    return created


def add_homework_attachment(*, homework, files, actor, request=None):
    if not _can_manage_homework(actor, homework) or homework.status != 'draft':
        raise PermissionDenied('You cannot add attachments to this homework.')
    return _add_attachments(
        parent=homework, files=files, actor=actor, model=HomeworkAttachment,
        relation_name='homework', kind='homework',
        max_count=_setting('MAX_ATTACHMENTS_PER_HOMEWORK', 10), request=request,
    )


def add_submission_attachment(*, submission, files, actor, request=None):
    if not _student_owns(actor, submission.student_enrollment):
        raise PermissionDenied('You cannot add attachments to this submission.')
    if submission.homework.status != 'published' or submission.status not in ('draft', 'returned'):
        raise ValidationError('Submission attachments cannot be changed.')
    if submission.homework.submission_type not in ('attachment', 'text_and_attachment'):
        raise ValidationError('This homework does not accept submission attachments.')
    return _add_attachments(
        parent=submission, files=files, actor=actor,
        model=HomeworkSubmissionAttachment, relation_name='submission',
        kind='submission', max_count=_setting('MAX_ATTACHMENTS_PER_SUBMISSION', 10),
        request=request,
    )


def _delete_file_safely(storage, name):
    try:
        storage.delete(name)
    except Exception:
        logger.exception('Attachment storage deletion failed after commit.')


@transaction.atomic
def delete_homework_attachment(*, attachment, actor, request=None):
    item = HomeworkAttachment.objects.select_for_update().select_related(
        'homework__teacher_assignment__teacher',
    ).get(pk=attachment.pk)
    if not _can_manage_homework(actor, item.homework) or item.homework.status != 'draft':
        raise PermissionDenied('You cannot delete this attachment.')
    storage, name = item.file.storage, item.file.name
    school_id, homework_id = item.homework.school_id, item.homework_id
    item.delete()
    _audit(
        school_id=school_id, actor=actor, action='attachment_delete',
        entity_type='homework', entity_id=homework_id, request=request,
        old_data={'attachment_deleted': True},
    )
    transaction.on_commit(partial(_delete_file_safely, storage, name))


@transaction.atomic
def delete_submission_attachment(*, attachment, actor, request=None):
    item = HomeworkSubmissionAttachment.objects.select_for_update().select_related(
        'submission__student_enrollment__student', 'submission__homework',
    ).get(pk=attachment.pk)
    submission = item.submission
    allowed_admin = _can_administer_school(actor, submission.homework.school_id)
    if not allowed_admin and not _student_owns(actor, submission.student_enrollment):
        raise PermissionDenied('You cannot delete this attachment.')
    if not allowed_admin and (
        submission.homework.status != 'published'
        or submission.status not in ('draft', 'returned')
    ):
        raise ValidationError('Submission attachments cannot be changed.')
    storage, name = item.file.storage, item.file.name
    school_id, submission_id = submission.homework.school_id, submission.pk
    item.delete()
    _audit(
        school_id=school_id, actor=actor, action='attachment_delete',
        entity_type='submission', entity_id=submission_id, request=request,
        old_data={'attachment_deleted': True},
    )
    transaction.on_commit(partial(_delete_file_safely, storage, name))