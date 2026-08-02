from datetime import date
from importlib import import_module

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from .models import (AcademicYear, Classroom, Parent, School, SchoolMembership,
                     Section, Student, StudentEnrollment, StudentGuardian,
                     Subject, Teacher, TeacherAssignment, User)


class Sprint4DFixtureMixin:
    password = 'Sprint4D-safe-test-password'

    def setUp(self):
        self.client = APIClient()
        self.school_a = School.objects.create(name='North School', code='NORTH')
        self.school_b = School.objects.create(name='South School', code='SOUTH')
        self.year_a = AcademicYear.objects.create(school=self.school_a, name='2026 A', start_date=date(2026, 1, 1), end_date=date(2026, 12, 31))
        self.year_b = AcademicYear.objects.create(school=self.school_b, name='2026 B', start_date=date(2026, 1, 1), end_date=date(2026, 12, 31))
        self.class_a = Classroom.objects.create(school=self.school_a, academic_year=self.year_a, name='A1', code='A1')
        self.class_b = Classroom.objects.create(school=self.school_b, academic_year=self.year_b, name='B1', code='B1')
        self.section_a = Section.objects.create(school=self.school_a, academic_year=self.year_a, classroom=self.class_a, name='A', code='A')
        self.section_b = Section.objects.create(school=self.school_b, academic_year=self.year_b, classroom=self.class_b, name='B', code='B')
        self.subject_a = Subject.objects.create(school=self.school_a, name='Math', code='M')
        self.subject_b = Subject.objects.create(school=self.school_b, name='Science', code='S')
        self.user = User.objects.create_user(username='multi', password=None, role='teacher', school=self.school_a, academic_year=self.year_a)
        self.teacher = Teacher.objects.create(user=self.user, school=self.school_a, academic_year=self.year_a, full_name='Multi Teacher')
        self.membership_a = SchoolMembership.objects.create(user=self.user, school=self.school_a, role='teacher', status='active', is_default=True)
        self.membership_b = SchoolMembership.objects.create(user=self.user, school=self.school_b, role='teacher', status='active')
        self.student_user = User.objects.create_user(username='student4d', password=None, role='student', school=self.school_a, academic_year=self.year_a)
        self.student = Student.objects.create(user=self.student_user, school=self.school_a, full_name='Student 4D', gender='male')
        self.enrollment = StudentEnrollment.objects.create(student=self.student, school=self.school_a, academic_year=self.year_a, classroom=self.class_a, section=self.section_a, status='active', is_current=True)
        self.student_membership = SchoolMembership.objects.create(user=self.student_user, school=self.school_a, role='student', status='active', is_default=True)
        self.super_admin = User.objects.create_user(username='root4d', password=None, role='super_admin', school=None)

    def auth(self, user=None, membership=None):
        user = user or self.user
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {RefreshToken.for_user(user).access_token}')
        if membership:
            self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {RefreshToken.for_user(user).access_token}', HTTP_X_SCHOOL_MEMBERSHIP_ID=str(membership.pk))


class SchoolMembershipModelTests(Sprint4DFixtureMixin, TestCase):
    def test_user_can_hold_teacher_memberships_in_two_schools(self):
        self.assertEqual(SchoolMembership.objects.filter(user=self.user, role='teacher', status='active').count(), 2)

    def test_same_user_school_role_is_unique(self):
        with self.assertRaises(ValidationError):
            SchoolMembership.objects.create(user=self.user, school=self.school_a, role='teacher')

    def test_same_school_allows_two_roles(self):
        membership = SchoolMembership.objects.create(user=self.user, school=self.school_a, role='parent')
        self.assertEqual(membership.role, 'parent')

    def test_only_one_default_membership(self):
        self.membership_b.is_default = True
        self.membership_b.save()
        self.membership_a.refresh_from_db()
        self.assertFalse(self.membership_a.is_default)

    def test_historical_membership_cannot_be_default(self):
        with self.assertRaises(ValidationError):
            SchoolMembership.objects.create(user=self.user, school=self.school_b, role='parent', status='historical', is_default=True)

    def test_membership_dates_must_be_ordered(self):
        with self.assertRaises(ValidationError):
            SchoolMembership.objects.create(user=self.user, school=self.school_b, role='parent', start_date=date(2026, 2, 1), end_date=date(2026, 1, 1))

    def test_active_student_membership_is_platform_unique(self):
        with self.assertRaises(ValidationError):
            SchoolMembership.objects.create(user=self.student_user, school=self.school_b, role='student', status='active')

    def test_student_historical_membership_is_allowed(self):
        item = SchoolMembership.objects.create(user=self.student_user, school=self.school_b, role='student', status='historical')
        self.assertEqual(item.access_mode, 'read_only')

    def test_active_membership_is_writable(self):
        self.assertEqual(self.membership_a.access_mode, 'read_write')

    def test_current_enrollment_is_platform_unique(self):
        with self.assertRaises(ValidationError):
            StudentEnrollment.objects.create(student=self.student, school=self.school_b, academic_year=self.year_b, classroom=self.class_b, section=self.section_b, status='active', is_current=True)

    def test_current_enrollment_must_be_active(self):
        self.enrollment.status = 'transferred'
        with self.assertRaises(ValidationError):
            self.enrollment.save()

    def test_historical_cross_school_enrollment_is_allowed(self):
        item = StudentEnrollment.objects.create(student=self.student, school=self.school_b, academic_year=self.year_b, classroom=self.class_b, section=self.section_b, status='transferred', is_current=False)
        self.assertEqual(item.school, self.school_b)

    def test_current_enrollment_updates_legacy_student_school(self):
        self.enrollment.is_current = False
        self.enrollment.status = 'transferred'
        self.enrollment.save()
        StudentEnrollment.objects.create(student=self.student, school=self.school_b, academic_year=self.year_b, classroom=self.class_b, section=self.section_b, status='active', is_current=True)
        self.student.refresh_from_db()
        self.assertEqual(self.student.school, self.school_b)

    def test_teacher_assignment_accepts_second_school_membership(self):
        assignment = TeacherAssignment.objects.create(teacher=self.teacher, school=self.school_b, academic_year=self.year_b, classroom=self.class_b, section=self.section_b, subject=self.subject_b)
        self.assertEqual(assignment.school, self.school_b)
    def test_data_migration_backfills_legacy_relationships_idempotently(self):
        parent_user = User.objects.create_user(username='legacy-parent', password=None, role='parent', school=self.school_a)
        parent = Parent.objects.create(user=parent_user, school=self.school_a, full_name='Legacy Parent')
        StudentGuardian.objects.create(parent=parent, student=self.student, relationship='guardian')
        SchoolMembership.objects.all().delete()
        migration = import_module('core.migrations.0020_multischool_memberships')
        from django.apps import apps
        migration.populate_school_memberships(apps, None)
        migration.populate_school_memberships(apps, None)
        self.assertTrue(SchoolMembership.objects.filter(user=self.student_user, role='student').exists())
        self.assertTrue(SchoolMembership.objects.filter(user=self.user, role='teacher', school=self.school_a).exists())
        self.assertEqual(SchoolMembership.objects.filter(user=parent_user, role='parent').count(), 1)