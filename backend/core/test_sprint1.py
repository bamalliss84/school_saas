from datetime import date

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from .models import (
    AcademicYear,
    Classroom,
    Parent,
    School,
    Section,
    Student,
    StudentEnrollment,
    StudentGuardian,
    Subject,
    Teacher,
    TeacherAssignment,
    User,
)


class SprintOneAPITestCase(APITestCase):
    password = 'Strong-test-password-123'

    @classmethod
    def setUpTestData(cls):
        cls.school_a = School.objects.create(name='School A', code='SA')
        cls.school_b = School.objects.create(name='School B', code='SB')
        cls.school_inactive = School.objects.create(
            name='Inactive School', code='SI', is_active=False,
        )

        cls.year_a = AcademicYear.objects.create(
            school=cls.school_a,
            name='2026 A',
            start_date=date(2026, 1, 1),
            end_date=date(2026, 12, 31),
        )
        cls.year_b = AcademicYear.objects.create(
            school=cls.school_b,
            name='2026 B',
            start_date=date(2026, 1, 1),
            end_date=date(2026, 12, 31),
        )
        cls.year_inactive = AcademicYear.objects.create(
            school=cls.school_inactive,
            name='2026 I',
            start_date=date(2026, 1, 1),
            end_date=date(2026, 12, 31),
        )

        cls.class_a = Classroom.objects.create(
            school=cls.school_a, academic_year=cls.year_a,
            name='Grade 1', code='G1',
        )
        cls.section_a = Section.objects.create(
            school=cls.school_a, academic_year=cls.year_a,
            classroom=cls.class_a, name='A', code='A',
        )
        cls.class_a_other = Classroom.objects.create(
            school=cls.school_a, academic_year=cls.year_a,
            name='Grade 2', code='G2',
        )
        cls.section_a_other = Section.objects.create(
            school=cls.school_a, academic_year=cls.year_a,
            classroom=cls.class_a_other, name='B', code='B',
        )
        cls.class_b = Classroom.objects.create(
            school=cls.school_b, academic_year=cls.year_b,
            name='Grade 1', code='G1',
        )
        cls.section_b = Section.objects.create(
            school=cls.school_b, academic_year=cls.year_b,
            classroom=cls.class_b, name='A', code='A',
        )
        cls.subject_a = Subject.objects.create(
            school=cls.school_a, name='Math', code='MATH',
        )
        cls.subject_a_2 = Subject.objects.create(
            school=cls.school_a, name='Science', code='SCI',
        )

        cls.super_admin = cls.create_user(
            'super', 'super_admin', school=None, academic_year=None,
        )
        cls.school_admin = cls.create_user(
            'school-admin', 'school_admin', cls.school_a, cls.year_a,
        )
        cls.teacher_user = cls.create_user(
            'teacher', 'teacher', cls.school_a, cls.year_a,
        )
        cls.parent_user = cls.create_user(
            'parent', 'parent', cls.school_a, cls.year_a,
        )
        cls.student_user = cls.create_user(
            'student', 'student', cls.school_a, cls.year_a,
        )
        cls.student_other_user = cls.create_user(
            'student-other', 'student', cls.school_a, cls.year_a,
        )
        cls.school_b_admin = cls.create_user(
            'school-b-admin', 'school_admin', cls.school_b, cls.year_b,
        )

        cls.teacher = Teacher.objects.create(
            school=cls.school_a, academic_year=cls.year_a,
            user=cls.teacher_user, full_name='Teacher One',
        )
        cls.parent = Parent.objects.create(
            school=cls.school_a, user=cls.parent_user,
            full_name='Parent One',
        )

        cls.student_own = Student.objects.create(
            school=cls.school_a, user=cls.student_user,
            full_name='Student Own', gender='male',
        )
        cls.student_other = Student.objects.create(
            school=cls.school_a, user=cls.student_other_user,
            full_name='Student Other', gender='female',
        )
        cls.student_b = Student.objects.create(
            school=cls.school_b, full_name='Student B', gender='male',
        )

        cls.enrollment_own = cls.create_enrollment(
            cls.student_own, cls.school_a, cls.year_a,
            cls.class_a, cls.section_a,
        )
        cls.enrollment_other = cls.create_enrollment(
            cls.student_other, cls.school_a, cls.year_a,
            cls.class_a_other, cls.section_a_other,
        )
        cls.enrollment_b = cls.create_enrollment(
            cls.student_b, cls.school_b, cls.year_b,
            cls.class_b, cls.section_b,
        )

        cls.guardian = StudentGuardian.objects.create(
            student=cls.student_own,
            parent=cls.parent,
            relationship='father',
            is_primary=True,
        )

        cls.assignment_math = TeacherAssignment.objects.create(
            teacher=cls.teacher, school=cls.school_a,
            academic_year=cls.year_a, classroom=cls.class_a,
            section=cls.section_a, subject=cls.subject_a,
        )
        cls.assignment_science = TeacherAssignment.objects.create(
            teacher=cls.teacher, school=cls.school_a,
            academic_year=cls.year_a, classroom=cls.class_a,
            section=cls.section_a, subject=cls.subject_a_2,
        )

    @classmethod
    def create_user(cls, username, role, school, academic_year):
        return User.objects.create_user(
            username=username,
            password=cls.password,
            role=role,
            school=school,
            academic_year=academic_year,
            first_name=username.title(),
        )

    @classmethod
    def create_enrollment(
        cls, student, school, academic_year, classroom, section,
        **kwargs,
    ):
        return StudentEnrollment.objects.create(
            student=student,
            school=school,
            academic_year=academic_year,
            classroom=classroom,
            section=section,
            status=kwargs.pop('status', 'active'),
            is_current=kwargs.pop('is_current', True),
            **kwargs,
        )

    def authenticate(self, user):
        self.client.force_authenticate(user=user)

    def results(self, response):
        self.assertIn('results', response.data)
        return response.data['results']

    def test_01_login_success_returns_tokens_and_user(self):
        response = self.client.post(reverse('token_obtain_pair'), {
            'username': self.teacher_user.username,
            'password': self.password,
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertEqual(response.data['user']['role'], 'teacher')
        self.assertEqual(response.data['user']['school']['id'], self.school_a.id)
        self.assertEqual(
            response.data['user']['linked_profile']['teacher_id'],
            self.teacher.id,
        )

    def test_02_inactive_user_cannot_login(self):
        user = self.create_user('inactive-user', 'student', self.school_a, self.year_a)
        User.objects.filter(pk=user.pk).update(is_active=False)
        response = self.client.post(reverse('token_obtain_pair'), {
            'username': user.username, 'password': self.password,
        })
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_03_user_of_inactive_school_cannot_login(self):
        user = self.create_user(
            'inactive-school-user', 'school_admin',
            self.school_inactive, self.year_inactive,
        )
        response = self.client.post(reverse('token_obtain_pair'), {
            'username': user.username, 'password': self.password,
        })
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_04_refresh_success(self):
        login = self.client.post(reverse('token_obtain_pair'), {
            'username': self.school_admin.username,
            'password': self.password,
        })
        response = self.client.post(reverse('token_refresh'), {
            'refresh': login.data['refresh'],
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)

    def test_05_logout_blacklists_refresh_token(self):
        login = self.client.post(reverse('token_obtain_pair'), {
            'username': self.school_admin.username,
            'password': self.password,
        })
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['access']}")
        response = self.client.post(reverse('token_logout'), {
            'refresh': login.data['refresh'],
        })
        self.assertEqual(response.status_code, status.HTTP_205_RESET_CONTENT)
        self.client.credentials()
        refresh_response = self.client.post(reverse('token_refresh'), {
            'refresh': login.data['refresh'],
        })
        self.assertEqual(
            refresh_response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_06_me_without_token_returns_401(self):
        response = self.client.get(reverse('current-user'))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_07_me_returns_correct_data_for_each_role(self):
        profiles = {
            self.super_admin: None,
            self.school_admin: None,
            self.teacher_user: {'teacher_id': self.teacher.id},
            self.parent_user: {'parent_id': self.parent.id},
            self.student_user: {'student_id': self.student_own.id},
        }
        for user, linked_profile in profiles.items():
            with self.subTest(role=user.role):
                client = APIClient()
                client.force_authenticate(user=user)
                response = client.get(reverse('current-user'))
                self.assertEqual(response.status_code, status.HTTP_200_OK)
                self.assertEqual(response.data['role'], user.role)
                self.assertEqual(response.data['linked_profile'], linked_profile)

    def test_08_super_admin_sees_students_from_all_schools(self):
        self.authenticate(self.super_admin)
        response = self.client.get(reverse('student-list'), {'page_size': 100})
        ids = {item['id'] for item in self.results(response)}
        self.assertIn(self.student_own.id, ids)
        self.assertIn(self.student_b.id, ids)

    def test_09_school_admin_sees_only_own_school(self):
        self.authenticate(self.school_admin)
        response = self.client.get(reverse('student-list'), {'page_size': 100})
        school_ids = {item['school']['id'] for item in self.results(response)}
        self.assertEqual(school_ids, {self.school_a.id})

    def test_10_school_admin_cannot_open_other_school_student(self):
        self.authenticate(self.school_admin)
        response = self.client.get(reverse('student-detail', args=[self.student_b.id]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_11_teacher_sees_only_assigned_students(self):
        self.authenticate(self.teacher_user)
        response = self.client.get(reverse('student-list'), {'page_size': 100})
        ids = {item['id'] for item in self.results(response)}
        self.assertEqual(ids, {self.student_own.id})

    def test_12_teacher_cannot_open_student_in_other_class(self):
        self.authenticate(self.teacher_user)
        response = self.client.get(
            reverse('student-detail', args=[self.student_other.id]),
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_13_parent_sees_only_linked_children(self):
        self.authenticate(self.parent_user)
        response = self.client.get(reverse('student-list'), {'page_size': 100})
        ids = {item['id'] for item in self.results(response)}
        self.assertEqual(ids, {self.student_own.id})

    def test_14_parent_cannot_open_unlinked_student(self):
        self.authenticate(self.parent_user)
        response = self.client.get(
            reverse('student-detail', args=[self.student_other.id]),
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_15_student_sees_only_self(self):
        self.authenticate(self.student_user)
        response = self.client.get(reverse('student-list'), {'page_size': 100})
        ids = {item['id'] for item in self.results(response)}
        self.assertEqual(ids, {self.student_own.id})

    def test_16_student_cannot_open_another_student(self):
        self.authenticate(self.student_user)
        response = self.client.get(
            reverse('student-detail', args=[self.student_other.id]),
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_17_user_without_school_sees_no_students(self):
        user = self.create_user('no-school', 'super_admin', None, None)
        User.objects.filter(pk=user.pk).update(role='school_admin')
        user.refresh_from_db()
        self.authenticate(user)
        response = self.client.get(reverse('student-list'))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_18_student_profile_is_student_only(self):
        self.authenticate(self.student_user)
        response = self.client.get(reverse('student-me-profile'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.student_own.id)
        self.authenticate(self.school_admin)
        denied = self.client.get(reverse('student-me-profile'))
        self.assertEqual(denied.status_code, status.HTTP_403_FORBIDDEN)

    def test_19_academic_history_is_ordered_and_scoped(self):
        old_year = AcademicYear.objects.create(
            school=self.school_a, name='2025 A',
            start_date=date(2025, 1, 1), end_date=date(2025, 12, 31),
        )
        old_class = Classroom.objects.create(
            school=self.school_a, academic_year=old_year,
            name='Old Grade', code='OLD',
        )
        old_section = Section.objects.create(
            school=self.school_a, academic_year=old_year,
            classroom=old_class, name='Old', code='OLD',
        )
        self.create_enrollment(
            self.student_own, self.school_a, old_year,
            old_class, old_section, is_current=False,
        )
        self.authenticate(self.student_user)
        response = self.client.get(
            reverse('student-academic-history', args=[self.student_own.id]),
            {'page_size': 100},
        )
        years = [item['academic_year']['name'] for item in self.results(response)]
        self.assertEqual(years, ['2026 A', '2025 A'])
        self.authenticate(self.student_other_user)
        denied = self.client.get(
            reverse('student-academic-history', args=[self.student_own.id]),
        )
        self.assertEqual(denied.status_code, status.HTTP_404_NOT_FOUND)

    def test_20_parent_children_returns_relationship_and_child(self):
        self.authenticate(self.parent_user)
        response = self.client.get(reverse('parent-children'))
        children = self.results(response)
        self.assertEqual(len(children), 1)
        self.assertEqual(children[0]['student']['id'], self.student_own.id)
        self.assertEqual(children[0]['relationship_type'], 'father')

    def test_21_parent_children_is_parent_only(self):
        self.authenticate(self.teacher_user)
        response = self.client.get(reverse('parent-children'))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_22_teacher_assignments_is_teacher_only(self):
        self.authenticate(self.teacher_user)
        response = self.client.get(reverse('teacher-assignments'), {'current': 'true'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(self.results(response)), 2)
        self.authenticate(self.school_admin)
        denied = self.client.get(reverse('teacher-assignments'))
        self.assertEqual(denied.status_code, status.HTTP_403_FORBIDDEN)

    def test_23_teacher_classes_are_unique(self):
        self.authenticate(self.teacher_user)
        response = self.client.get(reverse('teacher-classes'))
        self.assertEqual(len(self.results(response)), 1)

    def test_24_teacher_students_are_unique(self):
        self.authenticate(self.teacher_user)
        response = self.client.get(reverse('teacher-students'))
        ids = [item['id'] for item in self.results(response)]
        self.assertEqual(ids, [self.student_own.id])

    def test_25_teacher_subjects_are_unique(self):
        self.authenticate(self.teacher_user)
        response = self.client.get(reverse('teacher-subjects'))
        ids = {item['id'] for item in self.results(response)}
        self.assertEqual(ids, {self.subject_a.id, self.subject_a_2.id})

    def test_26_teacher_without_profile_returns_clear_404(self):
        user = self.create_user(
            'teacher-no-profile', 'teacher', self.school_a, self.year_a,
        )
        self.authenticate(user)
        response = self.client.get(reverse('teacher-assignments'))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data['message'], 'Not found.')

    def test_27_direct_out_of_scope_id_returns_formatted_404(self):
        self.authenticate(self.school_admin)
        response = self.client.get(reverse('student-detail', args=[self.student_b.id]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data, {
            'success': False, 'message': 'Not found.', 'errors': {},
        })

    def test_28_validation_errors_use_standard_format(self):
        self.authenticate(self.school_admin)
        response = self.client.post(reverse('token_logout'), {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        self.assertEqual(response.data['message'], 'Validation failed.')
        self.assertIn('refresh', response.data['errors'])

    def test_29_unauthenticated_error_uses_standard_format(self):
        response = self.client.get(reverse('student-list'))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data, {
            'success': False,
            'message': 'Authentication credentials were not provided.',
            'errors': {},
        })

    def test_30_student_list_is_paginated(self):
        self.authenticate(self.school_admin)
        response = self.client.get(reverse('student-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('count', response.data)
        self.assertIn('results', response.data)

    def test_31_student_search_ordering_and_active_filter(self):
        self.authenticate(self.school_admin)
        response = self.client.get(reverse('student-list'), {
            'search': 'Own', 'ordering': '-student_code', 'is_active': 'true',
        })
        ids = [item['id'] for item in self.results(response)]
        self.assertEqual(ids, [self.student_own.id])
    def test_32_login_rejects_inactive_school_user(self):
        User.objects.filter(pk=self.school_admin.pk).update(
            is_active_school_user=False,
        )
        response = self.client.post(reverse('token_obtain_pair'), {
            'username': self.school_admin.username,
            'password': self.password,
        })
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_33_refresh_rejects_school_user_disabled_after_issue(self):
        login = self.client.post(reverse('token_obtain_pair'), {
            'username': self.school_admin.username,
            'password': self.password,
        })
        User.objects.filter(pk=self.school_admin.pk).update(
            is_active_school_user=False,
        )
        response = self.client.post(reverse('token_refresh'), {
            'refresh': login.data['refresh'],
        })
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_34_refresh_rejects_school_disabled_after_issue(self):
        login = self.client.post(reverse('token_obtain_pair'), {
            'username': self.school_admin.username,
            'password': self.password,
        })
        School.objects.filter(pk=self.school_a.pk).update(is_active=False)
        response = self.client.post(reverse('token_refresh'), {
            'refresh': login.data['refresh'],
        })
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_35_old_access_cannot_use_me_after_school_user_disabled(self):
        login = self.client.post(reverse('token_obtain_pair'), {
            'username': self.school_admin.username,
            'password': self.password,
        })
        User.objects.filter(pk=self.school_admin.pk).update(
            is_active_school_user=False,
        )
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {login.data['access']}",
        )
        response = self.client.get(reverse('current-user'))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_36_old_access_cannot_list_students_after_school_disabled(self):
        login = self.client.post(reverse('token_obtain_pair'), {
            'username': self.school_admin.username,
            'password': self.password,
        })
        School.objects.filter(pk=self.school_a.pk).update(is_active=False)
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {login.data['access']}",
        )
        response = self.client.get(reverse('student-list'))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_37_user_cannot_blacklist_another_users_refresh_token(self):
        owner_login = self.client.post(reverse('token_obtain_pair'), {
            'username': self.school_admin.username,
            'password': self.password,
        })
        other_login = self.client.post(reverse('token_obtain_pair'), {
            'username': self.teacher_user.username,
            'password': self.password,
        })
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {owner_login.data['access']}",
        )
        response = self.client.post(reverse('token_logout'), {
            'refresh': other_login.data['refresh'],
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.client.credentials()
        refresh_response = self.client.post(reverse('token_refresh'), {
            'refresh': other_login.data['refresh'],
        })
        self.assertEqual(refresh_response.status_code, status.HTTP_200_OK)

    def test_38_super_admin_without_school_can_login_refresh_and_use_me(self):
        login = self.client.post(reverse('token_obtain_pair'), {
            'username': self.super_admin.username,
            'password': self.password,
        })
        self.assertEqual(login.status_code, status.HTTP_200_OK)
        self.assertIsNone(login.data['user']['school'])

        refresh = self.client.post(reverse('token_refresh'), {
            'refresh': login.data['refresh'],
        })
        self.assertEqual(refresh.status_code, status.HTTP_200_OK)

        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {login.data['access']}",
        )
        me = self.client.get(reverse('current-user'))
        self.assertEqual(me.status_code, status.HTTP_200_OK)
        self.assertEqual(me.data['role'], 'super_admin')

    def test_39_student_does_not_see_guardians(self):
        self.authenticate(self.student_user)
        detail = self.client.get(
            reverse('student-detail', args=[self.student_own.id]),
        )
        self.assertEqual(detail.status_code, status.HTTP_200_OK)
        self.assertEqual(detail.data['guardians'], [])

        profile = self.client.get(reverse('student-me-profile'))
        self.assertEqual(profile.status_code, status.HTTP_200_OK)
        self.assertEqual(profile.data['guardians'], [])

    def test_40_authorized_staff_roles_can_see_guardians(self):
        for user in (self.school_admin, self.teacher_user):
            with self.subTest(role=user.role):
                client = APIClient()
                client.force_authenticate(user=user)
                response = client.get(
                    reverse('student-detail', args=[self.student_own.id]),
                )
                self.assertEqual(response.status_code, status.HTTP_200_OK)
                self.assertEqual(len(response.data['guardians']), 1)
                self.assertEqual(
                    response.data['guardians'][0]['parent_id'],
                    self.parent.id,
                )
