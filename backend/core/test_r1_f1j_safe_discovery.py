"""Release 1.0 F1J — Safe Discovery acceptance tests.

Covers F1J-1..F1J-6 in docs/RELEASE1_ADMIN_F1F_F1N.md: scoped recipient
discovery for teachers and parents, signed recipient references, and the
Teacher -> Parent conversation start that consumes them.
"""
import time
from unittest.mock import patch

from django.core import signing
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from . import test_sprint3_exams
from .context import ensure_legacy_membership
from .models import (
    Conversation, Parent, SchoolMembership, Section, Student, StudentEnrollment,
    StudentGuardian, Subject, TeacherAssignment, User,
)

URL = '/api/v1/communication/recipient-options/'
START = '/api/v1/conversations/start/'


class ReleaseOneF1JSafeDiscoveryTests(APITestCase):
    password = test_sprint3_exams.SprintThreeExamPlatformTests.password
    setUpTestData = classmethod(
        test_sprint3_exams.SprintThreeExamPlatformTests.setUpTestData.__func__
    )

    def setUp(self):
        self.teacher_m = ensure_legacy_membership(self.teacher_user)
        self.parent_m = ensure_legacy_membership(self.parent_user)
        self.student_m = ensure_legacy_membership(self.student_user)
        self.admin_m = ensure_legacy_membership(self.admin_user)
        self.other_teacher_m = ensure_legacy_membership(self.other_teacher_user)

    def auth(self, user, membership):
        self.client.credentials(
            HTTP_AUTHORIZATION=f'Bearer {RefreshToken.for_user(user).access_token}',
            HTTP_X_SCHOOL_MEMBERSHIP_ID=str(membership.pk),
        )

    def discover(self, user, membership, **params):
        self.auth(user, membership)
        return self.client.get(URL, params)

    def teacher_ref(self, **params):
        response = self.discover(self.teacher_user, self.teacher_m, student_id=self.student.pk, **params)
        self.assertEqual(response.status_code, 200, response.content)
        return response.json()['results'][0]['recipient_ref']

    def start(self, **overrides):
        payload = {
            'conversation_type': 'teacher_parent', 'subject': 'Progress',
            'student_id': self.student.pk, 'teacher_assignment_id': self.assignment.pk,
        }
        payload.update(overrides)
        self.auth(self.teacher_user, self.teacher_m)
        return self.client.post(START, payload, format='json')

    # F1J-1 / F1J-3
    def test_teacher_discovers_only_guardians_of_taught_student_with_signed_refs(self):
        response = self.discover(self.teacher_user, self.teacher_m, student_id=self.student.pk)
        self.assertEqual(response.status_code, 200)
        rows = response.json()['results']
        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertEqual(row['display_name'], 'Parent One')
        self.assertEqual(row['role'], 'parent')
        self.assertEqual(row['relationship'], 'father')
        self.assertEqual(row['teacher_assignment_id'], self.assignment.pk)
        self.assertNotIn('membership_id', row)
        self.assertNotIn(str(self.parent_m.pk), [str(v) for v in row.values()])
        decoded = signing.loads(row['recipient_ref'], salt='communication-recipient-v1')
        self.assertEqual(decoded['m'], self.parent_m.pk)
        self.assertEqual(decoded['s'], self.school.pk)

    def test_teacher_rejected_for_student_in_untaught_section(self):
        section_b = Section.objects.create(
            school=self.school, academic_year=self.year, classroom=self.classroom, name='B',
        )
        outsider = Student.objects.create(
            school=self.school, full_name='Outsider', student_code='S3A-S90099', gender='male',
        )
        StudentEnrollment.objects.create(
            student=outsider, school=self.school, academic_year=self.year,
            classroom=self.classroom, section=section_b,
        )
        response = self.discover(self.teacher_user, self.teacher_m, student_id=outsider.pk)
        self.assertEqual(response.status_code, 403)

    # F1J-4
    def test_foreign_school_student_is_rejected_without_disclosure(self):
        response = self.discover(self.teacher_user, self.teacher_m, student_id=self.other_student.pk)
        self.assertEqual(response.status_code, 403)
        self.assertNotIn('Other Student', response.content.decode())
        missing = self.discover(self.teacher_user, self.teacher_m, student_id=999999)
        self.assertEqual(missing.status_code, response.status_code)

    def test_inactive_parent_membership_is_not_offered(self):
        second_user = User.objects.create_user(
            username='f1j-second-parent', password=self.password, role='parent', school=self.school,
        )
        second = Parent.objects.create(
            school=self.school, user=second_user, full_name='Suspended Parent', parent_code='S3A-P90077',
        )
        StudentGuardian.objects.create(student=self.student, parent=second, relationship='mother')
        membership = ensure_legacy_membership(second_user)
        SchoolMembership.objects.filter(pk=membership.pk).update(status='suspended', is_default=False)
        response = self.discover(self.teacher_user, self.teacher_m, student_id=self.student.pk)
        names = [row['display_name'] for row in response.json()['results']]
        self.assertEqual(names, ['Parent One'])

    def test_admin_and_student_roles_are_rejected(self):
        self.assertEqual(self.discover(self.admin_user, self.admin_m, student_id=self.student.pk).status_code, 403)
        self.assertEqual(self.discover(self.student_user, self.student_m, student_id=self.student.pk).status_code, 403)

    def test_student_id_is_validated(self):
        self.assertEqual(self.discover(self.teacher_user, self.teacher_m).status_code, 400)
        self.assertEqual(self.discover(self.teacher_user, self.teacher_m, student_id='abc').status_code, 400)

    # F1J-2
    def test_parent_discovers_only_teachers_of_linked_child(self):
        response = self.discover(self.parent_user, self.parent_m, student_id=self.student.pk)
        self.assertEqual(response.status_code, 200)
        rows = response.json()['results']
        self.assertEqual([(r['display_name'], r['role'], r['subject']) for r in rows], [('Teacher One', 'teacher', 'Math')])
        self.assertEqual(rows[0]['teacher_assignment_id'], self.assignment.pk)
        unlinked = self.discover(self.parent_user, self.parent_m, student_id=self.student_two.pk)
        self.assertEqual(unlinked.status_code, 403)

    # F1J-6
    def test_teacher_chooses_specific_owned_assignment(self):
        science = Subject.objects.create(school=self.school, name='Science', code='SCI')
        second = TeacherAssignment.objects.create(
            teacher=self.teacher, school=self.school, academic_year=self.year,
            classroom=self.classroom, section=self.section, subject=science,
        )
        response = self.discover(
            self.teacher_user, self.teacher_m, student_id=self.student.pk, teacher_assignment_id=second.pk,
        )
        self.assertEqual(response.status_code, 200)
        row = response.json()['results'][0]
        self.assertEqual(row['teacher_assignment_id'], second.pk)
        created = self.start(recipient_ref=row['recipient_ref'], teacher_assignment_id=second.pk)
        self.assertEqual(created.status_code, 201, created.content)

    def test_foreign_or_invalid_assignment_choice_is_rejected(self):
        foreign = self.discover(
            self.teacher_user, self.teacher_m, student_id=self.student.pk,
            teacher_assignment_id=self.other_assignment.pk,
        )
        self.assertEqual(foreign.status_code, 403)
        invalid = self.discover(
            self.teacher_user, self.teacher_m, student_id=self.student.pk, teacher_assignment_id='x',
        )
        self.assertEqual(invalid.status_code, 400)

    # F1J-5
    def test_teacher_parent_conversation_starts_from_valid_ref(self):
        response = self.start(recipient_ref=self.teacher_ref())
        self.assertEqual(response.status_code, 201, response.content)
        conversation = Conversation.objects.get(pk=response.json()['id'])
        self.assertSetEqual(
            set(conversation.participants.values_list('membership_id', flat=True)),
            {self.teacher_m.pk, self.parent_m.pk},
        )

    def test_conversation_requires_a_ref_and_rejects_tampering(self):
        self.assertEqual(self.start().status_code, 400)
        self.assertEqual(self.start(recipient_ref=self.teacher_ref() + 'x').status_code, 400)
        forged = signing.dumps(
            {'s': self.school.pk, 'k': 'parent', 'm': self.parent_m.pk, 'student': self.student.pk,
             'assignment': self.assignment.pk}, salt='another-salt', compress=True,
        )
        self.assertEqual(self.start(recipient_ref=forged).status_code, 400)
        self.assertFalse(Conversation.objects.filter(conversation_type='teacher_parent').exists())

    def test_ref_cannot_be_reused_for_another_student_or_assignment(self):
        ref = self.teacher_ref()
        self.assertEqual(self.start(recipient_ref=ref, student_id=self.student_two.pk).status_code, 400)
        self.assertEqual(
            self.start(recipient_ref=ref, teacher_assignment_id=self.other_assignment.pk).status_code, 400,
        )

    def test_ref_from_another_school_context_is_rejected(self):
        ref = self.teacher_ref()
        self.auth(self.other_teacher_user, self.other_teacher_m)
        response = self.client.post(START, {
            'conversation_type': 'teacher_parent', 'subject': 'Cross', 'student_id': self.student.pk,
            'teacher_assignment_id': self.assignment.pk, 'recipient_ref': ref,
        }, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertFalse(Conversation.objects.filter(conversation_type='teacher_parent').exists())

    def test_expired_ref_is_rejected(self):
        ref = self.teacher_ref()
        with patch('django.core.signing.time.time', return_value=time.time() + 3601):
            response = self.start(recipient_ref=ref)
        self.assertEqual(response.status_code, 400)
        self.assertIn('recipient_ref', response.content.decode())

    def test_historical_teacher_context_cannot_start_conversation_with_valid_ref(self):
        ref = self.teacher_ref()
        SchoolMembership.objects.filter(pk=self.teacher_m.pk).update(status='historical', is_default=False)
        response = self.start(recipient_ref=ref)
        self.assertEqual(response.status_code, 403)
        self.assertFalse(Conversation.objects.filter(conversation_type='teacher_parent').exists())

    def test_admin_cannot_use_parent_conversation_shortcut_without_scope(self):
        self.auth(self.admin_user, self.admin_m)
        response = self.client.post(START, {
            'conversation_type': 'teacher_parent', 'subject': 'Admin', 'student_id': self.student.pk,
            'teacher_assignment_id': self.assignment.pk, 'parent_membership_id': self.parent_m.pk,
        }, format='json')
        self.assertIn(response.status_code, (400, 403))
        self.assertFalse(Conversation.objects.filter(conversation_type='teacher_parent').exists())
