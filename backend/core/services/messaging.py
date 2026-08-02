import logging
from functools import partial

from django.conf import settings
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, ValidationError

from core.models import (
    Conversation, ConversationParticipant, Homework, HomeworkActionLog, Message,
    MessageAttachment, Parent, SchoolMembership, StudentEnrollment, StudentGuardian,
    TeacherAssignment,
)
from core.services.exam_results import request_audit_metadata
from core.services.homework import _delete_file_safely, validate_attachment
from core.services.notifications import create_notifications_bulk, run_notification_callback

logger = logging.getLogger(__name__)


def _audit(conversation, membership, action, request=None, metadata=None):
    HomeworkActionLog.objects.create(
        school=conversation.school, actor=membership.user, action=action,
        entity_type='conversation', entity_id=conversation.pk,
        new_data=metadata or {}, **request_audit_metadata(request),
    )


def conversations_for_membership(membership):
    if membership is None:
        return Conversation.objects.none()
    owned = Q(participants__membership=membership, participants__is_active=True, participants__left_at__isnull=True)
    if membership.role == 'school_admin':
        owned |= Q(conversation_type='school_support', school_id=membership.school_id)
    return Conversation.objects.filter(owned, school_id=membership.school_id).distinct().select_related(
        'school', 'created_by_membership__user', 'assigned_to_membership__user',
    ).prefetch_related('participants__membership__user')


def _validate_participants(school_id, memberships):
    items = list(SchoolMembership.objects.select_for_update().filter(pk__in=tuple(dict.fromkeys(memberships))).select_related('school'))
    if len(items) != len(set(memberships)) or any(item.school_id != school_id or item.status != 'active' or not item.school.is_active for item in items):
        raise ValidationError('Conversation participants are unavailable.')
    return items


@transaction.atomic
def start_conversation(*, creator_membership, participant_membership_ids, conversation_type, subject, related_type='', related_id=None, category='', priority='normal', request=None):
    if not creator_membership.can_write:
        raise PermissionDenied('A writable school context is required.')
    ids = tuple(dict.fromkeys((creator_membership.pk, *participant_membership_ids)))
    participants = _validate_participants(creator_membership.school_id, ids)
    candidates = Conversation.objects.select_for_update().filter(
        school_id=creator_membership.school_id, conversation_type=conversation_type,
        related_type=related_type, related_id=related_id, status__in=('open', 'in_progress'),
    ).annotate_participant_ids() if hasattr(Conversation.objects, 'annotate_participant_ids') else None
    if candidates is None and conversation_type != 'school_support':
        for candidate in Conversation.objects.select_for_update().filter(
            school_id=creator_membership.school_id, conversation_type=conversation_type,
            related_type=related_type, related_id=related_id, status__in=('open', 'in_progress'),
        ):
            existing=set(candidate.participants.filter(is_active=True).values_list('membership_id',flat=True))
            if existing == set(ids):
                return candidate, False
    conversation=Conversation.objects.create(
        school_id=creator_membership.school_id, conversation_type=conversation_type,
        subject=subject.strip()[:200], created_by_membership=creator_membership,
        related_type=related_type, related_id=related_id, category=category, priority=priority,
    )
    ConversationParticipant.objects.bulk_create([
        ConversationParticipant(conversation=conversation,membership=item,participant_role=item.role)
        for item in participants
    ])
    _audit(conversation,creator_membership,'conversation_started',request,{'participant_count':len(participants),'category':category})
    return conversation, True


def _active_target_membership(*, user_id, school_id, role):
    target = SchoolMembership.objects.filter(
        user_id=user_id, school_id=school_id, role=role, status='active', school__is_active=True,
    ).first()
    if target is None:
        raise ValidationError('Conversation participant is unavailable.')
    return target


def _assignment_for_context(*, membership, assignment_id, academic_year_id=None):
    queryset = TeacherAssignment.objects.filter(
        pk=assignment_id, school_id=membership.school_id, is_current=True,
    ).select_related('teacher')
    if academic_year_id:
        queryset = queryset.filter(academic_year_id=academic_year_id)
    assignment = queryset.first()
    if assignment is None:
        raise ValidationError('Teaching context was not found.')
    return assignment


def _enrollment_for_assignment(*, assignment, student_id=None, student_user_id=None):
    queryset = StudentEnrollment.objects.filter(
        school_id=assignment.school_id, academic_year_id=assignment.academic_year_id,
        classroom_id=assignment.classroom_id, section_id=assignment.section_id,
        is_current=True, status='active',
    ).select_related('student')
    if student_id:
        queryset = queryset.filter(student_id=student_id)
    if student_user_id:
        queryset = queryset.filter(student__user_id=student_user_id)
    enrollment = queryset.first()
    if enrollment is None:
        raise ValidationError('Student is outside the teaching context.')
    return enrollment


def start_teacher_student_conversation(*, creator_membership, assignment_id, subject, student_id=None, academic_year_id=None, request=None):
    if not creator_membership.can_write:
        raise PermissionDenied('A writable school context is required.')
    if creator_membership.role == 'teacher' and not student_id:
        raise ValidationError('A student is required for teacher-initiated conversations.')
    assignment = _assignment_for_context(
        membership=creator_membership, assignment_id=assignment_id,
        academic_year_id=academic_year_id,
    )
    if creator_membership.role == 'teacher':
        if assignment.teacher.user_id != creator_membership.user_id:
            raise PermissionDenied('Teaching context is outside your scope.')
        enrollment = _enrollment_for_assignment(assignment=assignment, student_id=student_id)
        target = _active_target_membership(
            user_id=enrollment.student.user_id, school_id=assignment.school_id, role='student',
        )
    elif creator_membership.role == 'student':
        enrollment = _enrollment_for_assignment(
            assignment=assignment, student_user_id=creator_membership.user_id,
        )
        target = _active_target_membership(
            user_id=assignment.teacher.user_id, school_id=assignment.school_id, role='teacher',
        )
    else:
        raise PermissionDenied('This role cannot start this conversation.')
    return start_conversation(
        creator_membership=creator_membership, participant_membership_ids=(target.pk,),
        conversation_type='teacher_student', subject=subject, related_type='student',
        related_id=enrollment.student_id, request=request,
    )


def _parent_for_student(*, enrollment, parent_membership_id=None, parent_id=None):
    queryset = SchoolMembership.objects.filter(
        school_id=enrollment.school_id, role='parent', status='active', school__is_active=True,
        user__parent_profile__students__student_id=enrollment.student_id,
    )
    if parent_membership_id:
        queryset = queryset.filter(pk=parent_membership_id)
    elif parent_id:
        queryset = queryset.filter(user__parent_profile_id=parent_id)
    else:
        raise ValidationError('A single parent recipient is required.')
    target = queryset.distinct().first()
    if target is None:
        raise ValidationError('Parent is not linked to this student.')
    return target


def start_teacher_parent_conversation(*, creator_membership, assignment_id, student_id, subject, parent_membership_id=None, parent_id=None, academic_year_id=None, request=None):
    if not creator_membership.can_write:
        raise PermissionDenied('A writable school context is required.')
    if not student_id:
        raise ValidationError('A student is required for parent conversations.')
    assignment = _assignment_for_context(
        membership=creator_membership, assignment_id=assignment_id,
        academic_year_id=academic_year_id,
    )
    enrollment = _enrollment_for_assignment(assignment=assignment, student_id=student_id)
    if creator_membership.role == 'teacher':
        if assignment.teacher.user_id != creator_membership.user_id:
            raise PermissionDenied('Teaching context is outside your scope.')
        target = _parent_for_student(
            enrollment=enrollment,
            parent_membership_id=parent_membership_id,
            parent_id=parent_id,
        )
    elif creator_membership.role == 'parent':
        if parent_membership_id or parent_id:
            raise ValidationError('Parents cannot select another parent recipient.')
        if not StudentGuardian.objects.filter(
            student_id=enrollment.student_id,
            parent__user_id=creator_membership.user_id,
        ).exists():
            raise PermissionDenied('Student is outside your guardian scope.')
        target = _active_target_membership(
            user_id=assignment.teacher.user_id,
            school_id=assignment.school_id,
            role='teacher',
        )
    else:
        raise PermissionDenied('This role cannot start a parent conversation.')
    return start_conversation(
        creator_membership=creator_membership,
        participant_membership_ids=(target.pk,), conversation_type='teacher_parent',
        subject=subject, related_type='student', related_id=enrollment.student_id, request=request,
    )


def start_homework_conversation(*, creator_membership, homework_id, subject, student_id=None, parent_membership_id=None, academic_year_id=None, request=None):
    if not creator_membership.can_write:
        raise PermissionDenied('A writable school context is required.')
    if creator_membership.role in ('teacher', 'parent') and not student_id:
        raise ValidationError('A student is required for this homework conversation.')
    homework = Homework.objects.filter(
        pk=homework_id, school_id=creator_membership.school_id,
        status__in=('published', 'closed'),
    ).select_related('teacher_assignment__teacher').first()
    if homework is None or (academic_year_id and homework.academic_year_id != academic_year_id):
        raise ValidationError('Homework context was not found.')
    assignment = homework.teacher_assignment
    if creator_membership.role == 'teacher':
        if assignment.teacher.user_id != creator_membership.user_id:
            raise PermissionDenied('Homework is outside your teaching scope.')
        enrollment = _enrollment_for_assignment(assignment=assignment, student_id=student_id)
        if parent_membership_id:
            target = _parent_for_student(
                enrollment=enrollment, parent_membership_id=parent_membership_id,
            )
        else:
            target = _active_target_membership(
                user_id=enrollment.student.user_id, school_id=homework.school_id, role='student',
            )
    elif creator_membership.role == 'student':
        enrollment = _enrollment_for_assignment(
            assignment=assignment, student_user_id=creator_membership.user_id,
        )
        target = _active_target_membership(
            user_id=assignment.teacher.user_id, school_id=homework.school_id, role='teacher',
        )
    elif creator_membership.role == 'parent':
        enrollment = _enrollment_for_assignment(assignment=assignment, student_id=student_id)
        if not StudentGuardian.objects.filter(
            student_id=enrollment.student_id, parent__user_id=creator_membership.user_id,
        ).exists():
            raise PermissionDenied('Student is outside your guardian scope.')
        target = _active_target_membership(
            user_id=assignment.teacher.user_id, school_id=homework.school_id, role='teacher',
        )
    else:
        raise PermissionDenied('This role cannot start a homework conversation.')
    return start_conversation(
        creator_membership=creator_membership, participant_membership_ids=(target.pk,),
        conversation_type='homework_discussion', subject=subject,
        related_type='homework', related_id=homework.pk, request=request,
    )


def _notify_school_support_created(*, conversation_id):
    conversation = Conversation.objects.get(pk=conversation_id)
    memberships = SchoolMembership.objects.filter(
        school_id=conversation.school_id, role='school_admin', status='active',
        school__is_active=True,
    ).exclude(pk=conversation.created_by_membership_id)
    return create_notifications_bulk(
        memberships=memberships, notification_type='school_support_created',
        title='New school support request', body=conversation.subject[:120],
        source_type='conversation', source_id=conversation.pk,
        payload={'action': {'route': 'school_support_detail', 'params': {'conversation_id': conversation.pk}}},
        deduplication_key_factory=lambda membership_id: f'school_support:{conversation.pk}:created:membership:{membership_id}',
    )


@transaction.atomic
def start_school_support_conversation(*, creator_membership, subject, category, priority='normal', request=None):
    if not creator_membership.can_write or creator_membership.role not in ('student', 'parent', 'teacher'):
        raise PermissionDenied('This role cannot start school support.')
    conversation, created = start_conversation(
        creator_membership=creator_membership, participant_membership_ids=(),
        conversation_type='school_support', subject=subject, category=category,
        priority=priority, request=request,
    )
    if created:
        transaction.on_commit(partial(
            run_notification_callback, _notify_school_support_created,
            conversation_id=conversation.pk,
        ))
    return conversation, created


def _notify_message(*, message_id):
    message=Message.objects.select_related('conversation','sender_membership').get(pk=message_id)
    memberships=SchoolMembership.objects.filter(
        conversation_participations__conversation=message.conversation,
        conversation_participations__is_active=True,
        conversation_participations__left_at__isnull=True,
        status='active', school__is_active=True,
    ).exclude(pk=message.sender_membership_id).distinct()
    kind='school_reply' if message.conversation.conversation_type=='school_support' and message.sender_membership.role=='school_admin' else 'message_received'
    return create_notifications_bulk(
        memberships=memberships,notification_type=kind,title='New message',body=message.body[:120],
        source_type='message',source_id=message.pk,
        payload={'action':{'route':'conversation_detail','params':{'conversation_id':message.conversation_id,'message_id':message.pk}}},
        deduplication_key_factory=lambda membership_id:f'message:{message.pk}:membership:{membership_id}',
    )


@transaction.atomic
def send_message(*, conversation, sender_membership, body, reply_to=None, request=None):
    item=Conversation.objects.select_for_update().get(pk=conversation.pk)
    if item.status in ('resolved','closed'):
        raise ValidationError('Conversation is not accepting replies.')
    if not sender_membership.can_write:
        raise PermissionDenied('A writable school context is required.')
    if not item.participants.filter(membership=sender_membership,is_active=True,can_reply=True,left_at__isnull=True).exists() and not (item.conversation_type=='school_support' and sender_membership.role=='school_admin' and sender_membership.school_id==item.school_id):
        raise PermissionDenied('You cannot reply to this conversation.')
    if sender_membership.role=='school_admin' and not item.participants.filter(membership=sender_membership).exists():
        ConversationParticipant.objects.create(conversation=item,membership=sender_membership,participant_role='school_admin')
    clean_body=(body or '').strip()
    limit=getattr(settings,'MAX_MESSAGE_LENGTH',4000)
    if not clean_body or len(clean_body)>limit or '<script' in clean_body.lower():
        raise ValidationError('Message body is invalid.')
    if reply_to and reply_to.conversation_id!=item.pk:
        raise ValidationError('Reply target is outside the conversation.')
    message=Message.objects.create(conversation=item,sender_membership=sender_membership,body=clean_body,reply_to=reply_to)
    item.last_message_at=message.created_at; item.save(update_fields=('last_message_at','updated_at'))
    _audit(item,sender_membership,'message_sent',request,{'message_id':message.pk})
    transaction.on_commit(partial(run_notification_callback,_notify_message,message_id=message.pk))
    return message


@transaction.atomic
def mark_conversation_read(*, conversation, membership):
    participant=ConversationParticipant.objects.select_for_update().filter(conversation=conversation,membership=membership,is_active=True).first()
    if participant is None:
        raise PermissionDenied('You cannot read this conversation.')
    participant.last_read_at=timezone.now(); participant.save(update_fields=('last_read_at',)); return participant


@transaction.atomic
def set_conversation_status(*, conversation, membership, status, resolution_note='', request=None):
    item = Conversation.objects.select_for_update().get(pk=conversation.pk)
    if membership.school_id != item.school_id or not membership.can_write:
        raise PermissionDenied('You cannot change this conversation.')
    is_admin = membership.role == 'school_admin'
    is_creator = membership.pk == item.created_by_membership_id
    if not is_admin and not is_creator:
        raise PermissionDenied('You cannot change this conversation.')
    if item.conversation_type != 'school_support' and status not in ('open', 'closed'):
        raise ValidationError('Invalid conversation status.')
    if not is_admin:
        if resolution_note:
            raise PermissionDenied('Only school administrators can add resolution notes.')
        allowed = (item.status == 'closed' and status == 'open') or (
            item.status != 'closed' and status == 'closed'
        )
        if not allowed:
            raise PermissionDenied('This status transition is not allowed.')
    transitions = {
        'open': {'in_progress', 'resolved', 'closed'},
        'in_progress': {'open', 'resolved', 'closed'},
        'resolved': {'open', 'closed'},
        'closed': {'open'},
    }
    old_status = item.status
    if status not in transitions.get(old_status, set()):
        raise ValidationError('Invalid conversation status transition.')
    now = timezone.now()
    item.status = status
    item.resolved_at = now if status == 'resolved' else None
    item.closed_at = now if status == 'closed' else None
    item.resolution_note = resolution_note.strip()[:1000] if is_admin and status in ('resolved', 'closed') else ''
    item.save(update_fields=(
        'status', 'resolved_at', 'closed_at', 'resolution_note', 'updated_at',
    ))
    action = {
        'open': 'conversation_reopened', 'closed': 'conversation_closed',
        'in_progress': 'support_marked_in_progress', 'resolved': 'support_resolved',
    }.get(status, 'support_status_changed')
    _audit(item, membership, action, request, {
        'old_status': old_status, 'new_status': status,
        'actor_membership_id': membership.pk,
        'has_resolution_note': bool(item.resolution_note),
        'resolution_note_length': len(item.resolution_note),
    })
    return item


@transaction.atomic
def add_message_attachments(*, message, membership, files):
    item = Message.objects.select_for_update().select_related('conversation').get(pk=message.pk)
    if not membership.can_write:
        raise PermissionDenied('A writable school context is required.')
    if item.sender_membership_id != membership.pk:
        raise PermissionDenied('Only the sender can add attachments.')
    if item.conversation.status in ('resolved', 'closed'):
        raise ValidationError('Conversation is not accepting attachments.')
    uploads = list(files)
    limit = getattr(settings, 'MAX_ATTACHMENTS_PER_MESSAGE', 5)
    existing = MessageAttachment.objects.select_for_update().filter(message=item).count()
    if not uploads or existing + len(uploads) > limit:
        raise ValidationError('Attachment count exceeds the allowed limit.')
    validated = [(uploaded, validate_attachment(uploaded, kind='message')) for uploaded in uploads]
    created = []
    stored = []
    try:
        for uploaded, metadata in validated:
            attachment = MessageAttachment(
                message=item, uploaded_by_membership=membership, **metadata,
            )
            attachment.file.save(metadata['original_name'], uploaded, save=False)
            stored.append((attachment.file.storage, attachment.file.name))
            attachment.save()
            created.append(attachment)
    except Exception:
        for storage, name in stored:
            try:
                storage.delete(name)
            except Exception:
                logger.exception('Message attachment cleanup failed after upload error.')
        raise
    return created


@transaction.atomic
def delete_message_attachment(*, attachment, membership):
    item = MessageAttachment.objects.select_for_update().select_related(
        'message__conversation',
    ).get(pk=attachment.pk)
    if not membership.can_write:
        raise PermissionDenied('A writable school context is required.')
    if item.uploaded_by_membership_id != membership.pk:
        raise PermissionDenied('Only the uploader can delete this attachment.')
    if item.message.conversation.status in ('resolved', 'closed'):
        raise ValidationError('Conversation attachments are read-only.')
    storage, name = item.file.storage, item.file.name
    item.delete()
    transaction.on_commit(partial(_delete_file_safely, storage, name))

def get_context_unread_conversation_counts(memberships):
    from django.db.models import Count, F
    ids=[item.pk for item in memberships]
    rows=ConversationParticipant.objects.filter(
        membership_id__in=ids,is_active=True,left_at__isnull=True,
    ).annotate(unread=Count('conversation__messages',filter=(~Q(conversation__messages__sender_membership_id=F('membership_id')) & (Q(last_read_at__isnull=True)|Q(conversation__messages__created_at__gt=F('last_read_at')))),distinct=True)).filter(unread__gt=0).values('membership_id').annotate(total=Count('id'))
    return {row['membership_id']:row['total'] for row in rows}


@transaction.atomic
def assign_school_support(*, conversation, actor_membership, assignee_membership, request=None):
    item=Conversation.objects.select_for_update().get(pk=conversation.pk)
    if item.conversation_type!='school_support' or actor_membership.role!='school_admin' or actor_membership.school_id!=item.school_id:
        raise PermissionDenied('You cannot assign this request.')
    if assignee_membership.school_id!=item.school_id or assignee_membership.role!='school_admin' or assignee_membership.status!='active':
        raise ValidationError('Support assignee is unavailable.')
    if item.status not in ('open', 'in_progress'):
        raise ValidationError('Only open support requests can be assigned.')
    item.assigned_to_membership = assignee_membership
    item.status = 'in_progress'
    item.resolved_at = None
    item.closed_at = None
    item.resolution_note = ''
    item.save(update_fields=(
        'assigned_to_membership', 'status', 'resolved_at', 'closed_at',
        'resolution_note', 'updated_at',
    ))
    _audit(
        item, actor_membership, 'support_assigned', request,
        {'assignee_membership_id': assignee_membership.pk},
    )
    return item


def _broadcast_callback(*, membership_ids, title, body, event_id, action):
    memberships=SchoolMembership.objects.filter(pk__in=membership_ids,status='active',school__is_active=True)
    return create_notifications_bulk(memberships=memberships,notification_type='system',title=title,body=body,payload={'action':action} if action else {},source_type='teacher_broadcast',source_id=event_id,deduplication_key_factory=lambda membership_id:f'broadcast:{event_id}:membership:{membership_id}')


def _validate_broadcast_action(*, action, actor_membership, assignment):
    action = action or {}
    if not action:
        return {}
    route = action.get('route')
    params = action.get('params') or {}
    if set(action) != {'route', 'params'} or not isinstance(params, dict):
        raise ValidationError('Broadcast action is invalid.')
    if route == 'school_home':
        if params:
            raise ValidationError('School home action does not accept parameters.')
    elif route == 'homework_detail':
        if set(params) != {'homework_id'}:
            raise ValidationError('Homework action is invalid.')
        if not Homework.objects.filter(
            pk=params['homework_id'], school_id=actor_membership.school_id,
            teacher_assignment=assignment, status__in=('published', 'closed'),
        ).exists():
            raise ValidationError('Homework action is outside the teaching context.')
    elif route == 'conversation_start':
        if set(params) != {'student_id'}:
            raise ValidationError('Conversation action is invalid.')
        _enrollment_for_assignment(assignment=assignment, student_id=params['student_id'])
    else:
        raise ValidationError('Broadcast action route is invalid.')
    return {'route': route, 'params': params}


@transaction.atomic
def broadcast_notification(*, actor_membership, teacher_assignment, student_ids, audience, title, body, action=None, request=None):
    from core.models import StudentEnrollment, StudentGuardian
    if not actor_membership.can_write or actor_membership.role not in ('teacher','school_admin'):
        raise PermissionDenied('You cannot broadcast notifications.')
    assignment=teacher_assignment
    if assignment.school_id!=actor_membership.school_id or not assignment.is_current:
        raise PermissionDenied('Teacher assignment is outside your context.')
    if actor_membership.role=='teacher' and assignment.teacher.user_id!=actor_membership.user_id:
        raise PermissionDenied('Teacher assignment is outside your context.')
    action = _validate_broadcast_action(
        action=action, actor_membership=actor_membership, assignment=assignment,
    )
    enrollments=StudentEnrollment.objects.filter(school_id=actor_membership.school_id,academic_year=assignment.academic_year,classroom=assignment.classroom,section=assignment.section,is_current=True,status='active').select_related('student')
    requested=set(student_ids or ())
    if requested:
        selected=enrollments.filter(student_id__in=requested)
        if selected.count()!=len(requested): raise ValidationError('One or more students are outside the assignment.')
        enrollments=selected
    student_ids=set(enrollments.values_list('student_id',flat=True)); roles={}
    if audience in ('students','students_and_parents'): roles['student']=set(enrollments.exclude(student__user__isnull=True).values_list('student__user_id',flat=True))
    if audience in ('parents','students_and_parents'): roles['parent']=set(StudentGuardian.objects.filter(student_id__in=student_ids,can_receive_notifications=True,parent__user__isnull=False).values_list('parent__user_id',flat=True))
    memberships=list(SchoolMembership.objects.filter(Q(*[Q(role=role,user_id__in=users) for role,users in roles.items()],_connector=Q.OR),school_id=actor_membership.school_id,status='active',school__is_active=True)) if roles else []
    event=HomeworkActionLog.objects.create(school_id=actor_membership.school_id,actor=actor_membership.user,action='teacher_broadcast_sent',entity_type='teacher_assignment',entity_id=assignment.pk,new_data={'recipient_count':len(memberships),'audience':audience},**request_audit_metadata(request))
    transaction.on_commit(partial(run_notification_callback,_broadcast_callback,membership_ids=tuple(item.pk for item in memberships),title=title[:200],body=body[:500],event_id=event.pk,action=action or {}))
    return {'recipient_count':len(memberships),'event_id':event.pk}