from datetime import date

from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from .models import (
    AcademicYear, Classroom, Parent, School, SchoolMembership, Section,
    Student, StudentEnrollment, StudentGuardian,
)

User = get_user_model()


class StudentAdminManagementTests(APITestCase):
    def setUp(self):
        self.school_a = School.objects.create(name='School A', code='F1CA')
        self.school_b = School.objects.create(name='School B', code='F1CB')
        self.year_a1, self.class_a1, self.section_a1 = self._structure(
            self.school_a, '2026-2027', date(2026, 9, 1), date(2027, 6, 30), 'A1',
        )
        self.year_a2, self.class_a2, self.section_a2 = self._structure(
            self.school_a, '2027-2028', date(2027, 9, 1), date(2028, 6, 30), 'A2',
        )
        self.year_b, self.class_b, self.section_b = self._structure(
            self.school_b, '2026-2027', date(2026, 9, 1), date(2027, 6, 30), 'B1',
        )
        self.admin = self._user('f1c-admin', 'school_admin', self.school_a)
        self.admin_membership = SchoolMembership.objects.create(
            user=self.admin, school=self.school_a, role='school_admin', status='active', is_default=True,
        )
        self.historical_admin = self._user('f1c-history', 'school_admin', self.school_a)
        self.historical_membership = SchoolMembership.objects.create(
            user=self.historical_admin, school=self.school_a, role='school_admin', status='historical',
        )
        self.teacher = self._user('f1c-teacher', 'teacher', self.school_a)
        self.teacher_membership = SchoolMembership.objects.create(
            user=self.teacher, school=self.school_a, role='teacher', status='active', is_default=True,
        )

    def _structure(self, school, name, start, end, code):
        year = AcademicYear.objects.create(school=school, name=name, start_date=start, end_date=end)
        classroom = Classroom.objects.create(school=school, academic_year=year, name=f'Class {code}', code=code)
        section = Section.objects.create(school=school, academic_year=year, classroom=classroom, name='Section 1', code=f'{code}-S1')
        return year, classroom, section

    def _user(self, username, role, school):
        return User.objects.create_user(username=username, password='password123', role=role, school=school)

    def _login(self, user, membership):
        response = self.client.post('/api/v1/auth/login/', {'username': user.username, 'password': 'password123'})
        self.assertEqual(response.status_code, 200, response.data)
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {response.data['access']}",
            HTTP_X_SCHOOL_MEMBERSHIP_ID=str(membership.pk),
        )

    def _student(self, school=None, user=None, name='Student One'):
        return Student.objects.create(school=school or self.school_a, user=user, full_name=name, gender='female')

    def _enrollment(self, student, year, classroom, section, **changes):
        values = {'status': 'active', 'is_current': True, 'start_date': year.start_date}
        values.update(changes)
        return StudentEnrollment.objects.create(
            student=student, school=year.school, academic_year=year,
            classroom=classroom, section=section, **values,
        )

    def test_student_create_update_lifecycle_and_read_shape_are_compatible(self):
        other = self._student(self.school_b, name='Other School')
        self._enrollment(other, self.year_b, self.class_b, self.section_b)
        self._login(self.admin, self.admin_membership)

        created = self.client.post('/api/v1/students/', {
            'school': self.school_b.id, 'user': 999, 'student_code': 'INJECTED',
            'full_name': 'New Student', 'gender': 'male', 'birth_date': '2015-02-03',
        })
        self.assertEqual(created.status_code, 201, created.data)
        student = Student.objects.get(pk=created.data['id'])
        self.assertEqual(student.school, self.school_a)
        self.assertIsNone(student.user)
        self.assertNotEqual(student.student_code, 'INJECTED')

        updated = self.client.patch(f'/api/v1/students/{student.id}/', {'full_name': 'Updated', 'is_active': False})
        self.assertEqual(updated.status_code, 200, updated.data)
        self.assertEqual(updated.data['full_name'], 'Updated')
        self.assertFalse(updated.data['is_active'])
        self.assertEqual(self.client.delete(f'/api/v1/students/{student.id}/').status_code, 405)

        listed = self.client.get('/api/v1/students/')
        self.assertEqual(listed.status_code, 200)
        self.assertEqual([row['id'] for row in listed.data['results']], [student.id])
        self.assertIn('current_enrollment', listed.data['results'][0])
        detail = self.client.get(f'/api/v1/students/{student.id}/')
        self.assertIn('guardians', detail.data)

    def test_student_write_guards_and_historical_reads(self):
        student = self._student()
        self._enrollment(student, self.year_a1, self.class_a1, self.section_a1)
        self._login(self.historical_admin, self.historical_membership)
        self.assertEqual(self.client.get(f'/api/v1/students/{student.id}/').status_code, 200)
        self.assertEqual(self.client.post('/api/v1/students/', {'full_name': 'Blocked', 'gender': 'male'}).status_code, 403)
        self.assertEqual(self.client.patch(f'/api/v1/students/{student.id}/', {'full_name': 'Blocked'}).status_code, 403)
        self._login(self.teacher, self.teacher_membership)
        self.assertEqual(self.client.post('/api/v1/students/', {'full_name': 'Blocked', 'gender': 'male'}).status_code, 403)

    def test_create_and_switch_current_enrollment_preserves_history_and_syncs_membership(self):
        student_user = self._user('f1c-student', 'student', self.school_a)
        student = self._student(user=student_user)
        self._login(self.admin, self.admin_membership)
        first = self.client.post(f'/api/v1/students/{student.id}/enrollments/', {
            'academic_year': self.year_a1.id, 'classroom': self.class_a1.id,
            'section': self.section_a1.id, 'status': 'active', 'is_current': True,
            'start_date': '2026-09-01',
        })
        self.assertEqual(first.status_code, 201, first.data)
        membership = SchoolMembership.objects.get(user=student_user, school=self.school_a, role='student')
        self.assertEqual(membership.status, 'active')

        second = self.client.post(f'/api/v1/students/{student.id}/enrollments/', {
            'academic_year': self.year_a2.id, 'classroom': self.class_a2.id,
            'section': self.section_a2.id, 'status': 'active', 'is_current': True,
            'start_date': '2027-09-01',
        })
        self.assertEqual(second.status_code, 201, second.data)
        old = StudentEnrollment.objects.get(pk=first.data['id'])
        self.assertFalse(old.is_current)
        self.assertTrue(StudentEnrollment.objects.filter(pk=old.pk).exists())
        self.assertEqual(StudentEnrollment.objects.filter(student=student, is_current=True).count(), 1)
        history = self.client.get(f'/api/v1/students/{student.id}/academic-history/')
        self.assertEqual(history.status_code, 200)
        self.assertEqual(len(history.data['results']), 2)

    def test_close_current_syncs_student_and_parent_memberships(self):
        student_user = self._user('f1c-student-close', 'student', self.school_a)
        student = self._student(user=student_user)
        enrollment = self._enrollment(student, self.year_a1, self.class_a1, self.section_a1)
        parent_user = self._user('f1c-parent', 'parent', self.school_a)
        parent = Parent.objects.create(user=parent_user, school=self.school_a, full_name='Parent')
        StudentGuardian.objects.create(parent=parent, student=student, relationship='guardian')
        from .services.identity import sync_parent_memberships, sync_student_memberships
        sync_student_memberships(student); sync_parent_memberships(student=student)
        self._login(self.admin, self.admin_membership)

        closed = self.client.patch(f'/api/v1/students/{student.id}/enrollments/{enrollment.id}/', {
            'status': 'graduated', 'is_current': False, 'end_date': '2027-06-30',
        })
        self.assertEqual(closed.status_code, 200, closed.data)
        enrollment.refresh_from_db()
        self.assertFalse(enrollment.is_current)
        self.assertEqual(SchoolMembership.objects.get(user=student_user, school=self.school_a, role='student').status, 'historical')
        self.assertEqual(SchoolMembership.objects.get(user=parent_user, school=self.school_a, role='parent').status, 'historical')

    def test_enrollment_validation_is_atomic_and_prevents_implicit_transfer(self):
        student = self._student()
        current = self._enrollment(student, self.year_a1, self.class_a1, self.section_a1)
        self._login(self.admin, self.admin_membership)
        invalid_cases = [
            {'academic_year': self.year_b.id, 'classroom': self.class_a2.id, 'section': self.section_a2.id, 'status': 'active', 'is_current': False},
            {'academic_year': self.year_a2.id, 'classroom': self.class_b.id, 'section': self.section_b.id, 'status': 'active', 'is_current': False},
            {'academic_year': self.year_a2.id, 'classroom': self.class_a2.id, 'section': self.section_a1.id, 'status': 'active', 'is_current': False},
            {'academic_year': self.year_a2.id, 'classroom': self.class_a2.id, 'section': self.section_a2.id, 'status': 'graduated', 'is_current': True},
        ]
        for payload in invalid_cases:
            response = self.client.post(f'/api/v1/students/{student.id}/enrollments/', payload)
            self.assertEqual(response.status_code, 400, response.data)
        duplicate = self.client.post(f'/api/v1/students/{student.id}/enrollments/', {
            'academic_year': self.year_a1.id, 'classroom': self.class_a1.id,
            'section': self.section_a1.id, 'status': 'active', 'is_current': False,
        })
        self.assertEqual(duplicate.status_code, 400)
        current.refresh_from_db(); self.assertTrue(current.is_current)

        StudentEnrollment.objects.filter(pk=current.pk).update(is_current=False, status='transferred')
        foreign_current = self._enrollment(student, self.year_b, self.class_b, self.section_b)
        student.refresh_from_db(); self.assertEqual(student.school, self.school_b)
        attempt = self.client.post(f'/api/v1/students/{student.id}/enrollments/', {
            'academic_year': self.year_a2.id, 'classroom': self.class_a2.id,
            'section': self.section_a2.id, 'status': 'active', 'is_current': True,
        })
        self.assertEqual(attempt.status_code, 400)
        foreign_current.refresh_from_db(); self.assertTrue(foreign_current.is_current)

    def test_enrollment_historical_write_and_identity_ownership_are_protected(self):
        student = self._student()
        enrollment = self._enrollment(student, self.year_a1, self.class_a1, self.section_a1)
        other = self._student(name='Other')
        self._login(self.admin, self.admin_membership)
        response = self.client.patch(f'/api/v1/students/{student.id}/enrollments/{enrollment.id}/', {
            'student': other.id, 'school': self.school_b.id, 'status': 'active',
        })
        self.assertEqual(response.status_code, 200, response.data)
        enrollment.refresh_from_db()
        self.assertEqual(enrollment.student, student)
        self.assertEqual(enrollment.school, self.school_a)
        self.assertEqual(self.client.delete(f'/api/v1/students/{student.id}/enrollments/{enrollment.id}/').status_code, 405)
        self._login(self.historical_admin, self.historical_membership)
        self.assertEqual(self.client.get(f'/api/v1/students/{student.id}/enrollments/').status_code, 200)
        self.assertEqual(self.client.patch(f'/api/v1/students/{student.id}/enrollments/{enrollment.id}/', {'status': 'graduated', 'is_current': False}).status_code, 403)
