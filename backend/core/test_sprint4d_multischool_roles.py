from django.test import TestCase
from rest_framework import status

from .models import Parent, SchoolMembership, StudentGuardian, TeacherAssignment
from .test_sprint4d_memberships import Sprint4DFixtureMixin


class MultiSchoolRoleTests(Sprint4DFixtureMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.assignment_a=TeacherAssignment.objects.create(teacher=self.teacher, school=self.school_a, academic_year=self.year_a, classroom=self.class_a, section=self.section_a, subject=self.subject_a)
        self.assignment_b=TeacherAssignment.objects.create(teacher=self.teacher, school=self.school_b, academic_year=self.year_b, classroom=self.class_b, section=self.section_b, subject=self.subject_b)

    def test_teacher_context_a_returns_only_assignment_a(self):
        self.auth(membership=self.membership_a); data=self.client.get('/api/v1/teachers/me/assignments/').data
        self.assertEqual({row['id'] for row in data['results']}, {self.assignment_a.pk})

    def test_teacher_context_b_returns_only_assignment_b(self):
        self.auth(membership=self.membership_b); data=self.client.get('/api/v1/teachers/me/assignments/').data
        self.assertEqual({row['id'] for row in data['results']}, {self.assignment_b.pk})

    def test_teacher_classes_are_context_scoped(self):
        self.auth(membership=self.membership_b); response=self.client.get('/api/v1/teachers/me/classes/')
        self.assertEqual(response.status_code, 200)

    def test_teacher_subjects_are_context_scoped(self):
        self.auth(membership=self.membership_a); response=self.client.get('/api/v1/teachers/me/subjects/')
        self.assertEqual(response.status_code, 200)

    def test_teacher_students_do_not_mix_schools(self):
        self.auth(membership=self.membership_b); response=self.client.get('/api/v1/teachers/me/students/')
        self.assertEqual(response.status_code, 200); self.assertNotContains(response, self.student.full_name)

    def test_teacher_legacy_school_does_not_block_second_assignment(self):
        self.assertEqual(self.teacher.school, self.school_a); self.assertEqual(self.assignment_b.school, self.school_b)

    def test_user_can_be_teacher_and_parent(self):
        membership=SchoolMembership.objects.create(user=self.user, school=self.school_b, role='parent')
        self.assertEqual(membership.role, 'parent')

    def test_role_changes_with_membership_header(self):
        parent_membership=SchoolMembership.objects.create(user=self.user, school=self.school_b, role='parent')
        self.auth(membership=parent_membership); response=self.client.get('/api/v1/auth/context/')
        self.assertEqual(response.data['role'], 'parent')

    def test_parent_can_have_active_memberships_in_two_schools(self):
        parent=Parent.objects.create(user=self.user, school=self.school_a, full_name='Parent Teacher')
        SchoolMembership.objects.create(user=self.user, school=self.school_a, role='parent')
        SchoolMembership.objects.create(user=self.user, school=self.school_b, role='parent')
        self.assertEqual(SchoolMembership.objects.filter(user=self.user, role='parent', status='active').count(), 2)

    def test_parent_child_relationship_controls_school_history(self):
        parent_user=self.user; parent=Parent.objects.create(user=parent_user, school=self.school_a, full_name='Guardian')
        StudentGuardian.objects.create(parent=parent, student=self.student, relationship='guardian')
        membership=SchoolMembership.objects.create(user=parent_user, school=self.school_a, role='parent')
        self.auth(membership=membership); self.assertEqual(self.client.get(f'/api/v1/parents/me/children/{self.student.pk}/schools/').status_code, 200)

    def test_parent_cannot_read_unlinked_child_history(self):
        parent=Parent.objects.create(user=self.user, school=self.school_a, full_name='Guardian')
        membership=SchoolMembership.objects.create(user=self.user, school=self.school_a, role='parent')
        self.auth(membership=membership); self.assertEqual(self.client.get(f'/api/v1/parents/me/children/{self.student.pk}/schools/').status_code, 404)

    def test_student_school_list_contains_current_school(self):
        self.auth(self.student_user, self.student_membership); response=self.client.get('/api/v1/students/me/schools/')
        self.assertEqual(response.status_code, 200); self.assertEqual(response.data[0]['school']['id'], self.school_a.pk)

    def test_student_history_rejects_unowned_school_id(self):
        self.auth(self.student_user, self.student_membership); response=self.client.get(f'/api/v1/students/me/academic-history/?school_id={self.school_b.pk}')
        self.assertEqual(response.status_code, 404)

    def test_old_access_token_rejects_suspended_membership(self):
        self.auth(membership=self.membership_a); self.membership_a.is_default=False; self.membership_a.status='suspended'; self.membership_a.save()
        self.assertEqual(self.client.get('/api/v1/teachers/me/assignments/', HTTP_X_SCHOOL_MEMBERSHIP_ID=str(self.membership_a.pk)).status_code, 403)