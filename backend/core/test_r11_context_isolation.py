"""Release 1.1 legacy cleanup: endpoints scope by the selected context, not user.school.

These tests use real JWT + X-School-Membership-ID requests (no force_authenticate), so
they exercise the active-context path that production uses.
"""

from django.test import TestCase

from .context import request_academic_year, request_role, request_school
from .models import Parent, SchoolMembership, StudentGuardian, TeacherAssignment
from .test_sprint4d_memberships import Sprint4DFixtureMixin


class _Req:
    """Minimal request double for the helper unit tests."""

    def __init__(self, user, **attrs):
        self.user = user
        for key, value in attrs.items():
            setattr(self, key, value)


class ContextHelperTests(Sprint4DFixtureMixin, TestCase):
    def test_active_context_wins_over_legacy_pointer(self):
        request = _Req(self.user, active_role='teacher', active_school=self.school_b,
                       active_academic_year=self.year_b)
        self.assertEqual(request_role(request), 'teacher')
        self.assertEqual(request_school(request), self.school_b)  # user.school is school A
        self.assertEqual(request_academic_year(request), self.year_b)

    def test_platform_owner_without_selection_is_global(self):
        self.assertIsNone(request_school(_Req(self.super_admin)))
        self.assertEqual(request_role(_Req(self.super_admin)), 'super_admin')

    def test_legacy_fallback_only_without_a_resolved_membership(self):
        request = _Req(self.user)
        self.assertEqual(request_school(request), self.school_a)
        self.assertEqual(request_academic_year(request), self.year_a)


class ContextIsolationApiTests(Sprint4DFixtureMixin, TestCase):
    def setUp(self):
        super().setUp()
        TeacherAssignment.objects.create(
            teacher=self.teacher, school=self.school_a, academic_year=self.year_a,
            classroom=self.class_a, section=self.section_a, subject=self.subject_a, is_current=True,
        )
        TeacherAssignment.objects.create(
            teacher=self.teacher, school=self.school_b, academic_year=self.year_b,
            classroom=self.class_b, section=self.section_b, subject=self.subject_b, is_current=True,
        )
        self.super_in_a = SchoolMembership.objects.create(
            user=self.super_admin, school=self.school_a, role='super_admin', status='active', is_default=True,
        )

    def summary(self, classroom):
        return self.client.get(f'/api/v1/attendance/class/{classroom.pk}/summary/')

    def test_super_admin_in_school_a_cannot_read_school_b_class_summary(self):
        self.auth(self.super_admin, self.super_in_a)
        self.assertEqual(self.summary(self.class_a).status_code, 200)
        self.assertEqual(self.summary(self.class_b).status_code, 404)

    def test_multi_school_teacher_summary_follows_the_selected_school(self):
        self.auth(membership=self.membership_b)
        self.assertEqual(self.summary(self.class_b).status_code, 200)
        self.assertEqual(self.summary(self.class_a).status_code, 404)
        self.auth(membership=self.membership_a)
        self.assertEqual(self.summary(self.class_a).status_code, 200)
        self.assertEqual(self.summary(self.class_b).status_code, 404)

    def test_school_list_is_scoped_to_the_selected_context(self):
        self.auth(self.super_admin, self.super_in_a)
        ids = {row['id'] for row in self.client.get('/api/v1/schools/').json()['results']}
        self.assertEqual(ids, {self.school_a.pk})
        self.auth(membership=self.membership_b)
        ids = {row['id'] for row in self.client.get('/api/v1/schools/').json()['results']}
        self.assertEqual(ids, {self.school_b.pk})

    def test_student_list_rejects_another_school_id_inside_a_school_context(self):
        self.auth(self.super_admin, self.super_in_a)
        response = self.client.get('/api/v1/students/', {'school_id': self.school_b.pk})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(self.client.get('/api/v1/students/', {'school_id': self.school_a.pk}).status_code, 200)

    def test_parent_children_use_the_selected_school(self):
        parent_user = self.user  # the teacher is also a parent (unique per user, school, role)
        parent = Parent.objects.create(user=parent_user, school=self.school_a, full_name='Parent Teacher')
        StudentGuardian.objects.create(parent=parent, student=self.student, relationship='father', is_primary=True)
        parent_a = SchoolMembership.objects.create(user=parent_user, school=self.school_a, role='parent', status='active')
        self.auth(membership=parent_a)
        response = self.client.get('/api/v1/parents/me/children/')
        self.assertEqual(response.status_code, 200, response.content)
        rows = response.json()
        rows = rows['results'] if isinstance(rows, dict) else rows
        self.assertEqual([row['student']['id'] for row in rows], [self.student.pk])
        # Selecting the teacher context in school B must not expose parent data.
        self.auth(membership=self.membership_b)
        self.assertIn(self.client.get('/api/v1/parents/me/children/').status_code, (403, 404))
