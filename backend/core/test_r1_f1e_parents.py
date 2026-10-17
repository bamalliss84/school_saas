from datetime import date
from unittest.mock import patch

from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from .models import (
    AcademicYear, Classroom, Parent, School, SchoolMembership, Section,
    Student, StudentEnrollment, StudentGuardian,
)
from .services.identity import sync_parent_memberships

User = get_user_model()


class ParentAdminManagementTests(APITestCase):
    def setUp(self):
        self.parent_sequence = 0
        self.school_a = School.objects.create(name='School A', code='F1EA')
        self.school_b = School.objects.create(name='School B', code='F1EB')
        self.year_a, self.class_a, self.section_a = self._structure(self.school_a, 'A')
        self.year_b, self.class_b, self.section_b = self._structure(self.school_b, 'B')
        self.admin = self._user('f1e-admin', 'school_admin', self.school_a)
        self.admin_membership = SchoolMembership.objects.create(
            user=self.admin, school=self.school_a, role='school_admin', status='active', is_default=True,
        )
        self.historical_admin = self._user('f1e-history', 'school_admin', self.school_a)
        self.historical_membership = SchoolMembership.objects.create(
            user=self.historical_admin, school=self.school_a, role='school_admin', status='historical',
        )
        self.student_a = self._student('Student A', self.school_a, self.year_a, self.class_a, self.section_a)
        self.student_a2 = self._student('Student A2', self.school_a, self.year_a, self.class_a, self.section_a)
        self.student_b = self._student('Student B', self.school_b, self.year_b, self.class_b, self.section_b)

    def _structure(self, school, code):
        year = AcademicYear.objects.create(
            school=school, name=f'2026-{code}', start_date=date(2026, 9, 1), end_date=date(2027, 6, 30),
        )
        classroom = Classroom.objects.create(school=school, academic_year=year, name=f'Class {code}', code=code)
        section = Section.objects.create(school=school, academic_year=year, classroom=classroom, name='One', code=f'{code}1')
        return year, classroom, section

    def _user(self, username, role, school):
        return User.objects.create_user(username=username, password='password123', role=role, school=school)

    def _student(self, name, school, year, classroom, section):
        student = Student.objects.create(school=school, full_name=name, gender='female')
        StudentEnrollment.objects.create(
            student=student, school=school, academic_year=year, classroom=classroom,
            section=section, status='active', is_current=True,
        )
        return student

    def _parent(self, name='Parent A', school=None, user=None):
        school = school or self.school_a
        self.parent_sequence += 1
        return Parent.objects.create(
            school=school, user=user, full_name=name,
            parent_code=f'{school.code}-P{self.parent_sequence:05d}',
        )

    def _login(self, user=None, membership=None):
        user = user or self.admin
        membership = membership or self.admin_membership
        response = self.client.post('/api/v1/auth/login/', {'username': user.username, 'password': 'password123'})
        self.assertEqual(response.status_code, 200, response.data)
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {response.data['access']}",
            HTTP_X_SCHOOL_MEMBERSHIP_ID=str(membership.pk),
        )

    def test_parent_list_detail_are_tenant_scoped_and_local_children_only(self):
        local = self._parent()
        StudentGuardian.objects.create(parent=local, student=self.student_a, relationship='father', is_primary=True)
        foreign = self._parent('Foreign', school=self.school_b)
        StudentGuardian.objects.create(parent=foreign, student=self.student_b, relationship='mother')
        shared = self._parent('Shared', school=self.school_b)
        StudentGuardian.objects.create(parent=shared, student=self.student_a2, relationship='guardian')
        StudentGuardian.objects.create(parent=shared, student=self.student_b, relationship='guardian')
        self._login()

        listed = self.client.get('/api/v1/parents/')
        self.assertEqual(listed.status_code, 200, listed.data)
        self.assertEqual({row['id'] for row in listed.data['results']}, {local.id, shared.id})
        shared_row = next(row for row in listed.data['results'] if row['id'] == shared.id)
        self.assertEqual([row['student']['id'] for row in shared_row['children']], [self.student_a2.id])
        self.assertFalse(shared_row['can_edit_profile'])
        self.assertEqual(self.client.get(f'/api/v1/parents/{foreign.id}/').status_code, 404)

    def test_create_parent_account_and_initial_guardian_is_atomic_and_rejects_injection(self):
        self._login()
        response = self.client.post('/api/v1/parents/', {
            'school': self.school_b.id, 'user': 999, 'user_id': 999, 'parent_code': 'INJECTED',
            'full_name': 'New Parent', 'phone': '0500000000',
            'account_username': 'new-parent', 'account_password': 'SecurePass123!',
            'student_id': self.student_a.id, 'relationship': 'mother', 'is_primary': True,
        }, format='json')
        self.assertEqual(response.status_code, 201, response.data)
        parent = Parent.objects.get(pk=response.data['id'])
        self.assertEqual(parent.school, self.school_a)
        self.assertNotEqual(parent.parent_code, 'INJECTED')
        self.assertEqual(parent.user.username, 'new-parent')
        link = StudentGuardian.objects.get(parent=parent, student=self.student_a)
        self.assertTrue(link.is_primary)
        membership = SchoolMembership.objects.get(user=parent.user, school=self.school_a, role='parent')
        self.assertEqual(membership.status, 'active')
        self.assertTrue(membership.is_default)

        collision = self.client.post('/api/v1/parents/', {
            'full_name': 'Collision', 'account_username': 'new-parent', 'account_password': 'AnotherPass123!',
            'student_id': self.student_a2.id, 'relationship': 'guardian',
        }, format='json')
        self.assertEqual(collision.status_code, 400)
        self.assertFalse(Parent.objects.filter(full_name='Collision').exists())

    def test_parent_create_rolls_back_account_profile_and_link_when_sync_fails(self):
        self._login()
        with patch('core.services.identity.sync_parent_memberships', side_effect=RuntimeError('sync failed')):
            response = self.client.post('/api/v1/parents/', {
                'full_name': 'Rollback Parent', 'account_username': 'rollback-parent',
                'account_password': 'SecurePass123!', 'student_id': self.student_a.id,
                'relationship': 'guardian',
            }, format='json')
        self.assertEqual(response.status_code, 500)
        self.assertFalse(User.objects.filter(username='rollback-parent').exists())
        self.assertFalse(Parent.objects.filter(full_name='Rollback Parent').exists())

    def test_existing_parent_link_requires_local_visibility_and_current_local_student(self):
        visible = self._parent()
        StudentGuardian.objects.create(parent=visible, student=self.student_a, relationship='father')
        foreign = self._parent('Foreign', school=self.school_b)
        StudentGuardian.objects.create(parent=foreign, student=self.student_b, relationship='father')
        self._login()

        linked = self.client.post(f'/api/v1/students/{self.student_a2.id}/guardians/', {
            'parent_id': visible.id, 'relationship': 'father', 'is_primary': False,
        }, format='json')
        self.assertEqual(linked.status_code, 201, linked.data)
        self.assertTrue(StudentGuardian.objects.filter(parent=visible, student=self.student_a2).exists())
        self.assertEqual(self.client.post(f'/api/v1/students/{self.student_a2.id}/guardians/', {
            'parent_id': foreign.id, 'relationship': 'father',
        }, format='json').status_code, 404)
        self.assertEqual(self.client.post(f'/api/v1/students/{self.student_b.id}/guardians/', {
            'parent_id': visible.id, 'relationship': 'father',
        }, format='json').status_code, 404)
        self.assertEqual(self.client.post(f'/api/v1/students/{self.student_a2.id}/guardians/', {
            'parent_id': visible.id, 'relationship': 'father',
        }, format='json').status_code, 400)

    def test_guardian_update_reconciles_primary_and_flags_and_primary_unlink_is_allowed(self):
        first = self._parent('First')
        second = self._parent('Second')
        first_link = StudentGuardian.objects.create(parent=first, student=self.student_a, relationship='father', is_primary=True)
        second_link = StudentGuardian.objects.create(parent=second, student=self.student_a, relationship='mother')
        self._login()

        updated = self.client.patch(f'/api/v1/students/{self.student_a.id}/guardians/{second_link.id}/', {
            'relationship': 'guardian', 'is_primary': True,
            'can_receive_notifications': False, 'can_receive_financial_alerts': False,
        }, format='json')
        self.assertEqual(updated.status_code, 200, updated.data)
        first_link.refresh_from_db(); second_link.refresh_from_db()
        self.assertFalse(first_link.is_primary)
        self.assertTrue(second_link.is_primary)
        self.assertEqual(second_link.relationship, 'guardian')
        self.assertFalse(second_link.can_receive_notifications)
        self.assertFalse(second_link.can_receive_financial_alerts)
        self.assertEqual(self.client.delete(
            f'/api/v1/students/{self.student_a.id}/guardians/{second_link.id}/'
        ).status_code, 204)
        self.assertFalse(StudentGuardian.objects.filter(pk=second_link.id).exists())
        self.assertFalse(StudentGuardian.objects.filter(student=self.student_a, is_primary=True).exists())

    def test_membership_derivation_handles_multiple_children_history_unlink_and_relink(self):
        user = self._user('derived-parent', 'parent', self.school_a)
        parent = self._parent(user=user)
        first = StudentGuardian.objects.create(parent=parent, student=self.student_a, relationship='father')
        second = StudentGuardian.objects.create(parent=parent, student=self.student_a2, relationship='father')
        sync_parent_memberships(parent=parent)
        membership = SchoolMembership.objects.get(user=user, school=self.school_a, role='parent')
        membership.is_default = True; membership.save()
        first.delete(); sync_parent_memberships(parent=parent)
        membership.refresh_from_db(); self.assertEqual(membership.status, 'active')
        enrollment = self.student_a2.enrollments.get()
        enrollment.is_current = False; enrollment.status = 'transferred'; enrollment.save()
        sync_parent_memberships(parent=parent)
        membership.refresh_from_db(); self.assertEqual(membership.status, 'historical')
        second.delete(); sync_parent_memberships(parent=parent)
        membership.refresh_from_db()
        self.assertEqual(membership.status, 'ended')
        self.assertFalse(membership.is_default)
        StudentGuardian.objects.create(parent=parent, student=self.student_a, relationship='father')
        sync_parent_memberships(parent=parent)
        membership.refresh_from_db(); self.assertEqual(membership.status, 'active')

    def test_multi_school_memberships_are_derived_independently(self):
        user = self._user('multi-parent', 'parent', self.school_a)
        parent = self._parent(user=user)
        link_a = StudentGuardian.objects.create(parent=parent, student=self.student_a, relationship='guardian')
        StudentGuardian.objects.create(parent=parent, student=self.student_b, relationship='guardian')
        sync_parent_memberships(parent=parent)
        self.assertEqual(set(SchoolMembership.objects.filter(user=user, role='parent', status='active').values_list('school_id', flat=True)), {self.school_a.id, self.school_b.id})
        link_a.delete(); sync_parent_memberships(parent=parent)
        self.assertEqual(SchoolMembership.objects.get(user=user, school=self.school_a, role='parent').status, 'ended')
        self.assertEqual(SchoolMembership.objects.get(user=user, school=self.school_b, role='parent').status, 'active')

    def test_historical_context_is_read_only_for_parent_and_guardian_writes(self):
        parent = self._parent()
        link = StudentGuardian.objects.create(parent=parent, student=self.student_a, relationship='guardian')
        self._login(self.historical_admin, self.historical_membership)
        self.assertEqual(self.client.get('/api/v1/parents/').status_code, 200)
        self.assertEqual(self.client.post('/api/v1/parents/', {
            'full_name': 'Blocked', 'student_id': self.student_a.id, 'relationship': 'guardian',
        }).status_code, 403)
        self.assertEqual(self.client.patch(f'/api/v1/parents/{parent.id}/', {'full_name': 'Blocked'}).status_code, 403)
        self.assertEqual(self.client.post(f'/api/v1/students/{self.student_a2.id}/guardians/', {
            'parent_id': parent.id, 'relationship': 'guardian',
        }).status_code, 403)
        self.assertEqual(self.client.patch(f'/api/v1/students/{self.student_a.id}/guardians/{link.id}/', {'relationship': 'other'}).status_code, 403)
        self.assertEqual(self.client.delete(f'/api/v1/students/{self.student_a.id}/guardians/{link.id}/').status_code, 403)

    def test_non_owner_school_cannot_patch_shared_parent_profile(self):
        shared = self._parent('Shared', school=self.school_b)
        StudentGuardian.objects.create(parent=shared, student=self.student_a, relationship='guardian')
        self._login()
        self.assertEqual(self.client.get(f'/api/v1/parents/{shared.id}/').status_code, 200)
        self.assertEqual(self.client.patch(f'/api/v1/parents/{shared.id}/', {'full_name': 'Hijacked'}).status_code, 403)
        shared.refresh_from_db(); self.assertEqual(shared.full_name, 'Shared')

    def test_transferred_student_relationship_is_readable_but_not_writable(self):
        parent = self._parent()
        link = StudentGuardian.objects.create(parent=parent, student=self.student_a, relationship='guardian')
        enrollment = self.student_a.enrollments.get()
        enrollment.is_current = False; enrollment.status = 'transferred'; enrollment.save()
        self._login()
        self.assertEqual(self.client.get(f'/api/v1/students/{self.student_a.id}/guardians/').status_code, 200)
        self.assertEqual(self.client.patch(
            f'/api/v1/students/{self.student_a.id}/guardians/{link.id}/', {'relationship': 'other'},
        ).status_code, 404)
        self.assertEqual(self.client.delete(
            f'/api/v1/students/{self.student_a.id}/guardians/{link.id}/'
        ).status_code, 404)
        self.assertTrue(StudentGuardian.objects.filter(pk=link.id).exists())

    def test_parent_mobile_children_contract_is_unchanged(self):
        user = self._user('mobile-parent', 'parent', self.school_a)
        parent = self._parent(user=user)
        StudentGuardian.objects.create(parent=parent, student=self.student_a, relationship='father', is_primary=True)
        sync_parent_memberships(parent=parent)
        membership = SchoolMembership.objects.get(user=user, school=self.school_a, role='parent')
        self._login(user, membership)
        response = self.client.get('/api/v1/parents/me/children/')
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data['results'][0]['student']['id'], self.student_a.id)
        self.assertEqual(response.data['results'][0]['relationship_type'], 'father')
        self.assertTrue(response.data['results'][0]['is_primary'])
