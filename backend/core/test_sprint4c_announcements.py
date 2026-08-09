from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from rest_framework import status

from .models import (
    Announcement, AnnouncementReceipt, Notification, Parent, SchoolMembership,
    StudentGuardian, TeacherAssignment, User,
)
from .services.announcements import (
    add_announcement_attachments, announcements_for_context, archive_announcement,
    close_announcement, create_announcement, delete_announcement_attachment,
    mark_announcement_read, publish_announcement, resolve_recipient_memberships,
    update_announcement,
)
from .test_sprint4d_memberships import Sprint4DFixtureMixin


class Sprint4CAnnouncementTests(Sprint4DFixtureMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.assignment = TeacherAssignment.objects.create(
            teacher=self.teacher,
            school=self.school_a,
            academic_year=self.year_a,
            classroom=self.class_a,
            section=self.section_a,
            subject=self.subject_a,
            is_current=True,
        )
        self.admin_user = User.objects.create_user(
            username='announcement-admin', password=None, role='school_admin',
            school=self.school_a, academic_year=self.year_a,
        )
        self.admin_membership = SchoolMembership.objects.create(
            user=self.admin_user, school=self.school_a, role='school_admin', status='active',
        )
        self.parent_user = User.objects.create_user(
            username='announcement-parent', password=None, role='parent', school=self.school_a,
        )
        self.parent = Parent.objects.create(
            user=self.parent_user, school=self.school_a, full_name='Announcement Parent',
        )
        StudentGuardian.objects.create(
            parent=self.parent, student=self.student, relationship='guardian',
            can_receive_notifications=True,
        )
        self.parent_membership = SchoolMembership.objects.create(
            user=self.parent_user, school=self.school_a, role='parent', status='active',
        )

    def create_item(self, **overrides):
        values = {
            'academic_year': self.year_a,
            'title': 'Important announcement',
            'body': 'Announcement body',
            'priority': 'normal',
            'audience_type': 'school',
            'target_roles': [],
            'include_parents': False,
        }
        values.update(overrides)
        return create_announcement(membership=self.admin_membership, **values)

    def test_school_admin_can_create_draft(self):
        item = self.create_item()
        self.assertEqual(item.status, 'draft')
        self.assertEqual(item.school, self.school_a)

    def test_teacher_can_only_target_own_assignment(self):
        item = create_announcement(
            membership=self.membership_a,
            academic_year=self.year_a,
            title='Teacher notice', body='Body', audience_type='teacher_assignment',
            teacher_assignment=self.assignment, include_parents=True,
        )
        self.assertEqual(item.teacher_assignment, self.assignment)

    def test_teacher_cannot_target_entire_school(self):
        with self.assertRaises(Exception):
            create_announcement(
                membership=self.membership_a,
                academic_year=self.year_a,
                title='Invalid', body='Body', audience_type='school',
            )

    def test_assignment_target_resolves_student_and_parent(self):
        item = self.create_item(
            audience_type='teacher_assignment', teacher_assignment=self.assignment,
            include_parents=True,
        )
        membership_ids = set(resolve_recipient_memberships(item).values_list('pk', flat=True))
        self.assertIn(self.student_membership.pk, membership_ids)
        self.assertIn(self.parent_membership.pk, membership_ids)
        self.assertNotIn(self.membership_b.pk, membership_ids)

    def test_publish_creates_receipts_atomically(self):
        item = self.create_item(audience_type='roles', target_roles=['student'])
        with self.captureOnCommitCallbacks(execute=True):
            publish_announcement(announcement=item, membership=self.admin_membership)
        item.refresh_from_db()
        self.assertEqual(item.status, 'published')
        self.assertTrue(AnnouncementReceipt.objects.filter(
            announcement=item, recipient_membership=self.student_membership,
        ).exists())

    def test_publish_creates_notification_after_commit(self):
        item = self.create_item(audience_type='roles', target_roles=['student'])
        with self.captureOnCommitCallbacks(execute=True):
            publish_announcement(announcement=item, membership=self.admin_membership)
        self.assertTrue(Notification.objects.filter(
            recipient_membership=self.student_membership,
            notification_type='announcement_published',
            source_id=item.pk,
        ).exists())

    def test_recipient_can_mark_announcement_read(self):
        item = self.create_item(audience_type='roles', target_roles=['student'])
        publish_announcement(announcement=item, membership=self.admin_membership)
        receipt = mark_announcement_read(announcement=item, membership=self.student_membership)
        self.assertIsNotNone(receipt.read_at)

    def test_non_recipient_cannot_mark_announcement_read(self):
        item = self.create_item(audience_type='roles', target_roles=['student'])
        publish_announcement(announcement=item, membership=self.admin_membership)
        with self.assertRaises(Exception):
            mark_announcement_read(announcement=item, membership=self.parent_membership)

    def test_close_published_announcement(self):
        item = self.create_item(audience_type='roles', target_roles=['student'])
        publish_announcement(announcement=item, membership=self.admin_membership)
        close_announcement(announcement=item, membership=self.admin_membership)
        item.refresh_from_db()
        self.assertEqual(item.status, 'closed')
        self.assertIsNotNone(item.closed_at)

    def test_cross_school_membership_never_receives_announcement(self):
        item = self.create_item()
        publish_announcement(announcement=item, membership=self.admin_membership)
        self.assertFalse(AnnouncementReceipt.objects.filter(
            announcement=item, recipient_membership=self.membership_b,
        ).exists())

    def test_unauthenticated_list_is_401(self):
        self.assertEqual(self.client.get('/api/v1/announcements/').status_code, status.HTTP_401_UNAUTHORIZED)

    def test_student_sees_only_published_receipt(self):
        published = self.create_item(audience_type='roles', target_roles=['student'])
        self.create_item(title='Draft hidden', audience_type='roles', target_roles=['student'])
        publish_announcement(announcement=published, membership=self.admin_membership)
        self.assertEqual(
            list(announcements_for_context(self.student_membership).values_list('pk', flat=True)),
            [published.pk],
        )
        self.auth(user=self.student_user, membership=self.student_membership)
        response = self.client.get('/api/v1/announcements/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual([row['id'] for row in response.data['results']], [published.pk])

    def test_student_cannot_create_announcement(self):
        self.auth(user=self.student_user, membership=self.student_membership)
        response = self.client.post('/api/v1/announcements/', {
            'academic_year': self.year_a.pk,
            'title': 'Invalid', 'body': 'Body', 'audience_type': 'school',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_read_endpoint_is_idempotent(self):
        item = self.create_item(audience_type='roles', target_roles=['student'])
        publish_announcement(announcement=item, membership=self.admin_membership)
        self.auth(user=self.student_user, membership=self.student_membership)
        url = f'/api/v1/announcements/{item.pk}/read/'
        first = self.client.post(url)
        second = self.client.post(url)
        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)

    def test_summary_is_manager_only(self):
        item = self.create_item(audience_type='roles', target_roles=['student'])
        publish_announcement(announcement=item, membership=self.admin_membership)
        self.auth(user=self.student_user, membership=self.student_membership)
        self.assertEqual(
            self.client.get(f'/api/v1/announcements/{item.pk}/summary/').status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_target_preview_returns_role_counts_without_pii(self):
        item = self.create_item(audience_type='teacher_assignment', teacher_assignment=self.assignment, include_parents=True)
        self.auth(user=self.admin_user, membership=self.admin_membership)
        response = self.client.get(f'/api/v1/announcements/{item.pk}/target-preview/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['eligible_count'], 2)
        self.assertEqual(response.data['by_role']['student'], 1)
        self.assertEqual(response.data['by_role']['parent'], 1)

    def test_invalid_filter_is_400(self):
        self.auth(user=self.admin_user, membership=self.admin_membership)
        self.assertEqual(
            self.client.get('/api/v1/announcements/', {'ordering': 'title'}).status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_historical_context_is_read_only_but_can_mark_read(self):
        item = self.create_item(audience_type='roles', target_roles=['student'])
        publish_announcement(announcement=item, membership=self.admin_membership)
        self.student_membership.is_default = False
        self.student_membership.status = 'historical'
        self.student_membership.save()
        self.auth(user=self.student_user, membership=self.student_membership)
        self.assertEqual(self.client.get('/api/v1/announcements/').status_code, 200)
        self.assertEqual(self.client.post(f'/api/v1/announcements/{item.pk}/read/').status_code, 200)
        self.assertEqual(self.client.post('/api/v1/announcements/', {}, format='json').status_code, 403)

    def test_openapi_contains_announcement_paths(self):
        self.super_admin.is_staff = True
        self.super_admin.save()
        self.auth(user=self.super_admin)
        response = self.client.get('/api/schema/')
        self.assertIn('/api/v1/announcements/', response.content.decode())

    def test_update_student_target_and_clear_it_when_mode_changes(self):
        item = self.create_item(
            audience_type='students', target_student_ids=(self.student.pk,),
        )
        self.assertEqual(list(item.target_students.all()), [self.student])
        item = update_announcement(
            announcement=item, membership=self.admin_membership,
            audience_type='roles', target_roles=['student'], target_student_ids=None,
        )
        self.assertFalse(item.target_students.exists())

    def test_student_target_rejects_missing_and_foreign_students(self):
        with self.assertRaises(Exception):
            self.create_item(audience_type='students')
        with self.assertRaises(Exception):
            self.create_item(audience_type='students', target_student_ids=(999999,))

    def test_invalid_target_combinations_are_rejected(self):
        invalid = (
            {'audience_type': 'school', 'target_roles': ['student']},
            {'audience_type': 'roles', 'include_parents': True},
            {'audience_type': 'school', 'classroom': self.class_a},
            {'audience_type': 'school', 'section': self.section_a},
            {'audience_type': 'school', 'teacher_assignment': self.assignment},
        )
        for values in invalid:
            with self.subTest(values=values), self.assertRaises(Exception):
                self.create_item(**values)

    def test_invalid_workflow_transitions_are_rejected(self):
        item = self.create_item(audience_type='roles', target_roles=['student'])
        with self.assertRaises(Exception):
            close_announcement(announcement=item, membership=self.admin_membership)
        with self.assertRaises(Exception):
            archive_announcement(announcement=item, membership=self.admin_membership)
        publish_announcement(announcement=item, membership=self.admin_membership)
        with self.assertRaises(Exception):
            publish_announcement(announcement=item, membership=self.admin_membership)
        with self.assertRaises(Exception):
            update_announcement(announcement=item, membership=self.admin_membership, title='No')

    def test_archive_published_and_closed_announcements(self):
        published = self.create_item(audience_type='roles', target_roles=['student'])
        publish_announcement(announcement=published, membership=self.admin_membership)
        archive_announcement(announcement=published, membership=self.admin_membership)
        published.refresh_from_db()
        self.assertEqual(published.status, 'archived')

        closed = self.create_item(audience_type='roles', target_roles=['student'])
        publish_announcement(announcement=closed, membership=self.admin_membership)
        close_announcement(announcement=closed, membership=self.admin_membership)
        archive_announcement(announcement=closed, membership=self.admin_membership)
        closed.refresh_from_db()
        self.assertEqual(closed.status, 'archived')

    def test_inactive_and_cross_school_memberships_cannot_manage(self):
        item = self.create_item()
        self.admin_membership.status = 'suspended'
        self.admin_membership.save(update_fields=('status',))
        with self.assertRaises(Exception):
            update_announcement(announcement=item, membership=self.admin_membership, title='No')
        with self.assertRaises(Exception):
            update_announcement(announcement=item, membership=self.membership_b, title='No')

    @override_settings(MEDIA_ROOT=None)
    def test_attachment_service_adds_and_deletes_draft_file(self):
        item = self.create_item()
        uploaded = SimpleUploadedFile('notice.txt', b'hello', content_type='text/plain')
        with self.settings(MEDIA_ROOT=self._temp_media_dir()):
            rows = add_announcement_attachments(
                announcement=item, membership=self.admin_membership, files=[uploaded],
            )
            self.assertEqual(len(rows), 1)
            with self.captureOnCommitCallbacks(execute=True):
                delete_announcement_attachment(
                    attachment=rows[0], membership=self.admin_membership,
                )
            self.assertFalse(item.attachments.exists())

    def _temp_media_dir(self):
        import tempfile
        return tempfile.mkdtemp(prefix='school-saas-announcements-')

    def test_attachment_service_rejects_published_and_limit(self):
        item = self.create_item(audience_type='roles', target_roles=['student'])
        publish_announcement(announcement=item, membership=self.admin_membership)
        uploaded = SimpleUploadedFile('notice.txt', b'hello', content_type='text/plain')
        with self.assertRaises(Exception):
            add_announcement_attachments(
                announcement=item, membership=self.admin_membership, files=[uploaded],
            )
        draft = self.create_item(title='Limited')
        with self.settings(MAX_ATTACHMENTS_PER_ANNOUNCEMENT=0), self.assertRaises(Exception):
            add_announcement_attachments(
                announcement=draft, membership=self.admin_membership, files=[uploaded],
            )

    def test_manager_api_create_update_publish_close_archive_and_summary(self):
        self.auth(user=self.admin_user, membership=self.admin_membership)
        created = self.client.post('/api/v1/announcements/', {
            'academic_year': self.year_a.pk, 'title': 'API notice', 'body': 'Body',
            'audience_type': 'roles', 'target_roles': ['student'],
        }, format='json')
        self.assertEqual(created.status_code, 201)
        pk = created.data['id']
        updated = self.client.patch(
            f'/api/v1/announcements/{pk}/', {'priority': 'high'}, format='json',
        )
        self.assertEqual(updated.status_code, 200)
        self.assertEqual(updated.data['priority'], 'high')
        self.assertEqual(self.client.post(f'/api/v1/announcements/{pk}/publish/').status_code, 200)
        summary = self.client.get(f'/api/v1/announcements/{pk}/summary/')
        self.assertEqual(summary.status_code, 200)
        self.assertEqual(summary.data['delivered_count'], 1)
        self.assertEqual(self.client.post(f'/api/v1/announcements/{pk}/close/').status_code, 200)
        self.assertEqual(self.client.post(f'/api/v1/announcements/{pk}/archive/').status_code, 200)

    def test_list_filters_read_state_search_and_dates(self):
        item = self.create_item(
            title='Searchable urgent', priority='urgent', audience_type='roles',
            target_roles=['student'],
        )
        publish_announcement(announcement=item, membership=self.admin_membership)
        self.auth(user=self.student_user, membership=self.student_membership)
        cases = (
            {'status': 'published'}, {'priority': 'urgent'}, {'audience_type': 'roles'},
            {'academic_year_id': self.year_a.pk}, {'unread': 'true'},
            {'search': 'Searchable'}, {'published_from': '2000-01-01T00:00:00Z'},
            {'published_to': '2100-01-01T00:00:00Z'}, {'ordering': 'created_at'},
        )
        for params in cases:
            with self.subTest(params=params):
                response = self.client.get('/api/v1/announcements/', params)
                self.assertEqual(response.status_code, 200)
                self.assertEqual([row['id'] for row in response.data['results']], [item.pk])
        self.client.post(f'/api/v1/announcements/{item.pk}/read/')
        self.assertEqual(
            self.client.get('/api/v1/announcements/', {'unread': 'false'}).data['count'], 1,
        )

    def test_attachment_api_requires_file_and_rejects_foreign_id(self):
        item = self.create_item()
        self.auth(user=self.admin_user, membership=self.admin_membership)
        url = f'/api/v1/announcements/{item.pk}/attachments/'
        self.assertEqual(self.client.post(url, {}, format='multipart').status_code, 400)
        self.assertEqual(self.client.get(url).status_code, 200)
        self.assertEqual(
            self.client.delete(f'{url}999999/').status_code, 404,
        )

    def test_attachment_api_uploads_and_deletes_file(self):
        item = self.create_item()
        self.auth(user=self.admin_user, membership=self.admin_membership)
        url = f'/api/v1/announcements/{item.pk}/attachments/'
        with self.settings(MEDIA_ROOT=self._temp_media_dir()):
            response = self.client.post(
                url,
                {'file': SimpleUploadedFile('notice.txt', b'hello', content_type='text/plain')},
                format='multipart',
            )
            self.assertEqual(response.status_code, 201)
            attachment_id = response.data[0]['id']
            with self.captureOnCommitCallbacks(execute=True):
                deleted = self.client.delete(f'{url}{attachment_id}/')
            self.assertEqual(deleted.status_code, 204)

    def test_recipient_can_open_school_support_inquiry(self):
        item = self.create_item(audience_type='roles', target_roles=['student'])
        publish_announcement(announcement=item, membership=self.admin_membership)
        self.auth(user=self.student_user, membership=self.student_membership)
        response = self.client.post(f'/api/v1/announcements/{item.pk}/inquiry/', {}, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['conversation_type'], 'school_support')

    def test_student_can_open_assignment_inquiry(self):
        item = self.create_item(
            audience_type='teacher_assignment', teacher_assignment=self.assignment,
        )
        publish_announcement(announcement=item, membership=self.admin_membership)
        self.auth(user=self.student_user, membership=self.student_membership)
        response = self.client.post(f'/api/v1/announcements/{item.pk}/inquiry/', {}, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['conversation_type'], 'teacher_student')

    def test_parent_assignment_inquiry_requires_student_id(self):
        item = self.create_item(
            audience_type='teacher_assignment', teacher_assignment=self.assignment,
            include_parents=True,
        )
        publish_announcement(announcement=item, membership=self.admin_membership)
        self.auth(user=self.parent_user, membership=self.parent_membership)
        response = self.client.post(f'/api/v1/announcements/{item.pk}/inquiry/', {}, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertIn('student_id', response.data)

    def test_inquiry_requires_receipt_and_enabled_state(self):
        item = self.create_item(audience_type='roles', target_roles=['student'], allow_inquiry=False)
        publish_announcement(announcement=item, membership=self.admin_membership)
        self.auth(user=self.student_user, membership=self.student_membership)
        self.assertEqual(
            self.client.post(f'/api/v1/announcements/{item.pk}/inquiry/', {}).status_code, 400,
        )
        self.auth(user=self.parent_user, membership=self.parent_membership)
        self.assertEqual(
            self.client.post(f'/api/v1/announcements/{item.pk}/inquiry/', {}).status_code, 404,
        )
