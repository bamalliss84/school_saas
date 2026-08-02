import tempfile
from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError, transaction
from django.test import override_settings
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from . import test_sprint3_exams
from .context import ensure_legacy_membership
from .models import (
    Conversation, HomeworkActionLog, MessageAttachment, Notification, Parent,
    SchoolMembership, StudentGuardian, User,
)
from .services.messaging import (
    add_message_attachments, broadcast_notification, send_message,
    set_conversation_status, start_conversation, start_school_support_conversation,
    start_teacher_parent_conversation,
)
from .services.notifications import _safe_payload


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class Sprint4B1CommunicationHardeningTests(APITestCase):
    password = test_sprint3_exams.SprintThreeExamPlatformTests.password
    setUpTestData = classmethod(
        test_sprint3_exams.SprintThreeExamPlatformTests.setUpTestData.__func__
    )

    def setUp(self):
        self.teacher_m = ensure_legacy_membership(self.teacher_user)
        self.student_m = ensure_legacy_membership(self.student_user)
        self.parent_m = ensure_legacy_membership(self.parent_user)
        self.admin_m = ensure_legacy_membership(self.admin_user)
        self.other_teacher_m = ensure_legacy_membership(self.other_teacher_user)
        self.parent_two_user = User.objects.create_user(
            username='second-parent', password=self.password, role='parent', school=self.school,
        )
        self.parent_two = Parent.objects.create(
            school=self.school, user=self.parent_two_user, full_name='Parent Two',
            parent_code='S3A-P90002',
        )
        StudentGuardian.objects.create(
            student=self.student, parent=self.parent_two, relationship='mother',
        )
        self.parent_two_m = ensure_legacy_membership(self.parent_two_user)

    def auth(self, user, membership):
        self.client.credentials(
            HTTP_AUTHORIZATION=f'Bearer {RefreshToken.for_user(user).access_token}',
            HTTP_X_SCHOOL_MEMBERSHIP_ID=str(membership.pk),
        )

    def pdf(self, name='safe.pdf'):
        return SimpleUploadedFile(name, b'%PDF-1.4 safe', content_type='application/pdf')

    def support(self):
        return start_school_support_conversation(
            creator_membership=self.student_m, subject='Private request',
            category='technical_issue',
        )[0]

    def message(self):
        conversation = start_conversation(
            creator_membership=self.teacher_m,
            participant_membership_ids=(self.student_m.pk,),
            conversation_type='teacher_student', subject='Files',
        )[0]
        return send_message(
            conversation=conversation, sender_membership=self.teacher_m, body='Attachment',
        )

    def test_teacher_parent_has_exactly_one_parent(self):
        conversation, _ = start_teacher_parent_conversation(
            creator_membership=self.teacher_m, assignment_id=self.assignment.pk,
            student_id=self.student.pk, parent_membership_id=self.parent_m.pk,
            subject='Private guardian conversation', academic_year_id=self.year.pk,
        )
        self.assertSetEqual(
            set(conversation.participants.values_list('membership_id', flat=True)),
            {self.teacher_m.pk, self.parent_m.pk},
        )

    def test_other_guardian_cannot_see_private_conversation(self):
        conversation, _ = start_teacher_parent_conversation(
            creator_membership=self.teacher_m, assignment_id=self.assignment.pk,
            student_id=self.student.pk, parent_membership_id=self.parent_m.pk,
            subject='Private', academic_year_id=self.year.pk,
        )
        self.auth(self.parent_two_user, self.parent_two_m)
        self.assertEqual(
            self.client.get(f'/api/v1/conversations/{conversation.pk}/').status_code, 404,
        )

    def test_unlinked_parent_rejected(self):
        unlinked_user = User.objects.create_user(username='unlinked', role='parent', school=self.school)
        unlinked = Parent.objects.create(
            school=self.school, user=unlinked_user, full_name='Unlinked', parent_code='S3A-P90003',
        )
        membership = ensure_legacy_membership(unlinked_user)
        with self.assertRaises(ValidationError):
            start_teacher_parent_conversation(
                creator_membership=self.teacher_m, assignment_id=self.assignment.pk,
                student_id=self.student.pk, parent_membership_id=membership.pk,
                subject='No', academic_year_id=self.year.pk,
            )
        self.assertIsNotNone(unlinked.pk)

    def test_cross_school_teacher_parent_rejected(self):
        with self.assertRaises((PermissionDenied, ValidationError)):
            start_teacher_parent_conversation(
                creator_membership=self.other_teacher_m, assignment_id=self.assignment.pk,
                student_id=self.student.pk, parent_membership_id=self.parent_m.pk,
                subject='No', academic_year_id=self.other_year.pk,
            )

    def test_school_support_notification_after_commit(self):
        with self.captureOnCommitCallbacks(execute=False) as callbacks:
            conversation, _ = start_school_support_conversation(
                creator_membership=self.student_m, subject='Short subject', category='other',
            )
            self.assertFalse(Notification.objects.filter(source_id=conversation.pk).exists())
        self.assertEqual(len(callbacks), 1)
        callbacks[0]()
        notice = Notification.objects.get(source_id=conversation.pk)
        self.assertEqual(notice.recipient_membership, self.admin_m)
        self.assertEqual(notice.notification_type, 'school_support_created')
        self.assertNotIn('complaint', notice.body.lower())

    def test_school_support_rollback_discards_notification(self):
        with self.captureOnCommitCallbacks(execute=True):
            try:
                with transaction.atomic():
                    start_school_support_conversation(
                        creator_membership=self.student_m, subject='Rollback', category='other',
                    )
                    raise RuntimeError('rollback')
            except RuntimeError:
                pass
        self.assertFalse(Notification.objects.filter(notification_type='school_support_created').exists())

    def test_school_support_no_active_admin_does_not_fail(self):
        self.admin_m.status = 'suspended'
        self.admin_m.is_default = False
        self.admin_m.save(update_fields=('status', 'is_default'))
        with self.captureOnCommitCallbacks(execute=True):
            conversation, _ = start_school_support_conversation(
                creator_membership=self.student_m, subject='No admin', category='other',
            )
        self.assertTrue(Conversation.objects.filter(pk=conversation.pk).exists())
        self.assertFalse(Notification.objects.filter(source_id=conversation.pk).exists())

    def test_school_support_retry_deduplicates(self):
        with self.captureOnCommitCallbacks(execute=True):
            conversation, _ = start_school_support_conversation(
                creator_membership=self.student_m, subject='Retry', category='other',
            )
        from .services.messaging import _notify_school_support_created
        _notify_school_support_created(conversation_id=conversation.pk)
        self.assertEqual(Notification.objects.filter(source_id=conversation.pk).count(), 1)

    def test_two_valid_attachments_are_atomic(self):
        created = add_message_attachments(
            message=self.message(), membership=self.teacher_m,
            files=[self.pdf('one.pdf'), self.pdf('two.pdf')],
        )
        self.assertEqual(len(created), 2)

    def test_invalid_second_attachment_creates_nothing(self):
        message = self.message()
        invalid = SimpleUploadedFile('bad.exe', b'bad', content_type='application/octet-stream')
        with self.assertRaises(ValidationError):
            add_message_attachments(
                message=message, membership=self.teacher_m, files=[self.pdf(), invalid],
            )
        self.assertFalse(MessageAttachment.objects.filter(message=message).exists())

    def test_storage_second_failure_cleans_first(self):
        message = self.message()
        storage = MessageAttachment._meta.get_field('file').storage
        with patch.object(storage, 'save', side_effect=['messages/one.pdf', OSError('down')]), patch.object(storage, 'delete') as delete:
            with self.assertRaises(OSError):
                add_message_attachments(
                    message=message, membership=self.teacher_m,
                    files=[self.pdf('one.pdf'), self.pdf('two.pdf')],
                )
        delete.assert_called_once_with('messages/one.pdf')
        self.assertFalse(MessageAttachment.objects.filter(message=message).exists())

    def test_closed_conversation_rejects_attachment(self):
        message = self.message()
        message.conversation.status = 'closed'
        from django.utils import timezone
        message.conversation.closed_at = timezone.now()
        message.conversation.save(update_fields=('status', 'closed_at'))
        with self.assertRaises(ValidationError):
            add_message_attachments(message=message, membership=self.teacher_m, files=[self.pdf()])

    def test_historical_membership_rejects_attachment(self):
        message = self.message()
        self.teacher_m.status = 'historical'
        self.teacher_m.is_default = False
        self.teacher_m.save(update_fields=('status', 'is_default'))
        with self.assertRaises(PermissionDenied):
            add_message_attachments(message=message, membership=self.teacher_m, files=[self.pdf()])

    def test_support_status_and_note_are_atomic(self):
        item = set_conversation_status(
            conversation=self.support(), membership=self.admin_m, status='resolved',
            resolution_note='Resolved safely',
        )
        self.assertEqual(item.status, 'resolved')
        self.assertEqual(item.resolution_note, 'Resolved safely')
        self.assertIsNotNone(item.resolved_at)
        self.assertIsNone(item.closed_at)

    def test_status_failure_rolls_back_note(self):
        conversation = self.support()
        with patch('core.services.messaging._audit', side_effect=RuntimeError('audit down')):
            with self.assertRaises(RuntimeError):
                set_conversation_status(
                    conversation=conversation, membership=self.admin_m, status='resolved',
                    resolution_note='Must roll back',
                )
        conversation.refresh_from_db()
        self.assertEqual(conversation.status, 'open')
        self.assertEqual(conversation.resolution_note, '')

    def test_student_cannot_write_resolution_note(self):
        with self.assertRaises(PermissionDenied):
            set_conversation_status(
                conversation=self.support(), membership=self.student_m, status='closed',
                resolution_note='Admin-only',
            )

    def test_reopen_clears_resolution_metadata(self):
        item = set_conversation_status(
            conversation=self.support(), membership=self.admin_m, status='resolved',
            resolution_note='Done',
        )
        item = set_conversation_status(
            conversation=item, membership=self.admin_m, status='open',
        )
        self.assertEqual(item.resolution_note, '')
        self.assertIsNone(item.resolved_at)
        log = HomeworkActionLog.objects.filter(entity_id=item.pk).first()
        self.assertEqual(log.action, 'conversation_reopened')
        self.assertNotIn('Done', str(log.new_data))

    def test_audit_mapping_for_in_progress_and_closed(self):
        item = set_conversation_status(
            conversation=self.support(), membership=self.admin_m, status='in_progress',
        )
        self.assertTrue(HomeworkActionLog.objects.filter(
            entity_id=item.pk, action='support_marked_in_progress',
        ).exists())
        set_conversation_status(
            conversation=item, membership=self.admin_m, status='closed',
            resolution_note='Closed',
        )
        self.assertTrue(HomeworkActionLog.objects.filter(
            entity_id=item.pk, action='conversation_closed',
        ).exists())

    def test_broadcast_school_home_action(self):
        with self.captureOnCommitCallbacks(execute=True):
            result = broadcast_notification(
                actor_membership=self.teacher_m, teacher_assignment=self.assignment,
                student_ids=[self.student.pk], audience='students', title='Notice', body='Safe',
                action={'route': 'school_home', 'params': {}},
            )
        self.assertEqual(result['recipient_count'], 1)

    def test_broadcast_unknown_route_rejected_by_service(self):
        with self.assertRaises(ValidationError):
            broadcast_notification(
                actor_membership=self.teacher_m, teacher_assignment=self.assignment,
                student_ids=[], audience='students', title='Notice', body='Safe',
                action={'route': 'https://evil.example', 'params': {}},
            )

    def test_broadcast_nested_secret_rejected(self):
        with self.assertRaises(ValidationError):
            broadcast_notification(
                actor_membership=self.teacher_m, teacher_assignment=self.assignment,
                student_ids=[], audience='students', title='Notice', body='Safe',
                action={'route': 'school_home', 'params': {'secret': 'x'}},
            )

    def test_recursive_payload_rejects_secrets(self):
        for payload in (
            {'token': 'x'}, {'action': {'Password': 'x'}},
            {'items': [{'AUTHORIZATION': 'x'}]},
        ):
            with self.subTest(payload=payload), self.assertRaises(ValidationError):
                _safe_payload(payload)

    def test_payload_rejects_depth_size_and_objects(self):
        deep = current = {}
        for _ in range(10):
            current['child'] = {}
            current = current['child']
        for payload in (deep, {'body': 'x' * 5000}, {'object': object()}):
            with self.subTest(kind=type(payload)), self.assertRaises(ValidationError):
                _safe_payload(payload)

    def test_safe_flutter_action_passes(self):
        action = {'action': {'route': 'homework_detail', 'params': {'homework_id': 1}}}
        self.assertEqual(_safe_payload(action), action)

    def test_database_constraints(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            Conversation.objects.create(
                school=self.school, conversation_type='school_support', subject='Bad',
                created_by_membership=self.student_m, category='',
            )

    def test_parent_can_start_private_conversation_with_child_teacher(self):
        conversation, created = start_teacher_parent_conversation(
            creator_membership=self.parent_m,
            assignment_id=self.assignment.pk,
            student_id=self.student.pk,
            subject='Question about my child',
            academic_year_id=self.year.pk,
        )
        self.assertTrue(created)
        self.assertSetEqual(
            set(conversation.participants.values_list('membership_id', flat=True)),
            {self.parent_m.pk, self.teacher_m.pk},
        )

    def test_parent_cannot_select_another_parent_recipient(self):
        with self.assertRaises(ValidationError):
            start_teacher_parent_conversation(
                creator_membership=self.parent_m,
                assignment_id=self.assignment.pk,
                student_id=self.student.pk,
                parent_membership_id=self.parent_two_m.pk,
                subject='Invalid parent selection',
                academic_year_id=self.year.pk,
            )

    def test_teacher_conversation_requires_explicit_student(self):
        from .services.messaging import start_teacher_student_conversation
        with self.assertRaises(ValidationError):
            start_teacher_student_conversation(
                creator_membership=self.teacher_m,
                assignment_id=self.assignment.pk,
                subject='No implicit first student',
                academic_year_id=self.year.pk,
            )

    def test_historical_membership_cannot_delete_message_attachment(self):
        from .services.messaging import delete_message_attachment
        message = self.message()
        attachment = add_message_attachments(
            message=message,
            membership=self.teacher_m,
            files=[self.pdf('history.pdf')],
        )[0]
        self.teacher_m.status = 'historical'
        self.teacher_m.is_default = False
        self.teacher_m.save(update_fields=('status', 'is_default'))
        with self.assertRaises(PermissionDenied):
            delete_message_attachment(
                attachment=attachment,
                membership=self.teacher_m,
            )
        self.assertTrue(MessageAttachment.objects.filter(pk=attachment.pk).exists())

    def test_resolved_support_request_cannot_be_assigned(self):
        from .services.messaging import assign_school_support
        conversation = set_conversation_status(
            conversation=self.support(),
            membership=self.admin_m,
            status='resolved',
            resolution_note='Finished',
        )
        with self.assertRaises(ValidationError):
            assign_school_support(
                conversation=conversation,
                actor_membership=self.admin_m,
                assignee_membership=self.admin_m,
            )
