"""Release 1.0 F1I — Communications acceptance tests (docs/RELEASE1_ADMIN_F1F_F1N.md).

Posts the exact payload shapes sent by the Web admin portal (OperationsPage)
for announcement audiences and the School Support workflow, and verifies
tenant isolation and historical read-only behaviour on the server.
"""
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from . import test_sprint3_exams
from .context import ensure_legacy_membership
from .models import Announcement, Conversation, SchoolMembership
from .services.messaging import start_school_support_conversation


def web_payload(**overrides):
    """Mirror of OperationsPage.saveAnnouncement."""
    payload = {
        'title': 'اجتماع', 'body': 'تفاصيل', 'priority': 'normal', 'audience_type': 'school',
        'target_roles': [], 'classroom': None, 'section': None, 'include_parents': False, 'allow_inquiry': False,
    }
    payload.update(overrides)
    return payload


class ReleaseOneF1ICommunicationsTests(APITestCase):
    password = test_sprint3_exams.SprintThreeExamPlatformTests.password
    setUpTestData = classmethod(
        test_sprint3_exams.SprintThreeExamPlatformTests.setUpTestData.__func__
    )

    def setUp(self):
        self.admin_m = ensure_legacy_membership(self.admin_user)
        self.student_m = ensure_legacy_membership(self.student_user)
        self.teacher_m = ensure_legacy_membership(self.teacher_user)
        self.auth(self.admin_user, self.admin_m)

    def auth(self, user, membership):
        self.client.credentials(
            HTTP_AUTHORIZATION=f'Bearer {RefreshToken.for_user(user).access_token}',
            HTTP_X_SCHOOL_MEMBERSHIP_ID=str(membership.pk),
        )

    def announce(self, **overrides):
        return self.client.post('/api/v1/announcements/', web_payload(**overrides), format='json')

    # F1I-2
    def test_web_role_audience_payload_is_accepted(self):
        response = self.announce(audience_type='roles', target_roles=['parent', 'teacher'])
        self.assertEqual(response.status_code, 201, response.content)
        item = Announcement.objects.get(pk=response.json()['id'])
        self.assertEqual((item.audience_type, sorted(item.target_roles), item.status), ('roles', ['parent', 'teacher'], 'draft'))

    def test_empty_role_audience_is_rejected(self):
        response = self.announce(audience_type='roles', target_roles=[])
        # Regression: model validation used to escape as an unhandled 500.
        self.assertEqual(response.status_code, 400, response.content)
        self.assertIn('target role', response.content.decode())

    def test_web_classroom_and_section_payloads_are_accepted(self):
        classroom = self.announce(audience_type='classroom', classroom=self.classroom.pk, include_parents=True)
        self.assertEqual(classroom.status_code, 201, classroom.content)
        section = self.announce(audience_type='section', classroom=self.classroom.pk, section=self.section.pk)
        self.assertEqual(section.status_code, 201, section.content)
        item = Announcement.objects.get(pk=section.json()['id'])
        self.assertEqual((item.classroom_id, item.section_id), (self.classroom.pk, self.section.pk))

    def test_foreign_classroom_or_section_is_rejected(self):
        self.assertEqual(self.announce(audience_type='classroom', classroom=self.other_classroom.pk).status_code, 400)
        self.assertEqual(
            self.announce(audience_type='section', classroom=self.classroom.pk, section=self.other_section.pk).status_code, 400,
        )
        self.assertFalse(Announcement.objects.filter(school=self.school).exists())

    def test_historical_admin_cannot_create_announcements(self):
        SchoolMembership.objects.filter(pk=self.admin_m.pk).update(status='historical', is_default=False)
        self.assertEqual(self.announce().status_code, 403)

    # F1I-4
    def support(self):
        return start_school_support_conversation(
            creator_membership=self.student_m, subject='تعديل بيانات', category='profile_update',
        )[0]

    def test_admin_assigns_and_resolves_support_with_note(self):
        ticket = self.support()
        assigned = self.client.post(f'/api/v1/school-inbox/{ticket.pk}/assign/', {}, format='json')
        self.assertEqual(assigned.status_code, 200, assigned.content)
        self.assertEqual(assigned.json()['status'], 'in_progress')
        resolved = self.client.post(
            f'/api/v1/school-inbox/{ticket.pk}/status/', {'status': 'resolved', 'resolution_note': 'تم التحديث'}, format='json',
        )
        self.assertEqual(resolved.status_code, 200, resolved.content)
        ticket.refresh_from_db()
        self.assertEqual(ticket.status, 'resolved')

    def test_support_actions_are_admin_only_and_school_scoped(self):
        ticket = self.support()
        self.auth(self.teacher_user, self.teacher_m)
        self.assertIn(self.client.post(f'/api/v1/school-inbox/{ticket.pk}/assign/', {}, format='json').status_code, (403, 404))
        other_admin = SchoolMembership.objects.create(
            user=self.other_teacher_user, school=self.other_school, role='school_admin', status='active', is_default=False,
        )
        self.auth(self.other_teacher_user, other_admin)
        self.assertEqual(self.client.post(f'/api/v1/school-inbox/{ticket.pk}/assign/', {}, format='json').status_code, 404)
        self.assertEqual(self.client.get(f'/api/v1/school-inbox/{ticket.pk}/').status_code, 404)
        ticket.refresh_from_db()
        self.assertEqual(ticket.status, 'open')

    def test_historical_admin_reads_but_cannot_change_support(self):
        ticket = self.support()
        SchoolMembership.objects.filter(pk=self.admin_m.pk).update(status='historical', is_default=False)
        self.assertEqual(self.client.get(f'/api/v1/school-inbox/{ticket.pk}/').status_code, 200)
        self.assertEqual(self.client.post(f'/api/v1/school-inbox/{ticket.pk}/assign/', {}, format='json').status_code, 403)
        self.assertEqual(
            self.client.post(f'/api/v1/school-inbox/{ticket.pk}/status/', {'status': 'resolved'}, format='json').status_code, 403,
        )
        self.assertEqual(Conversation.objects.get(pk=ticket.pk).status, 'open')
