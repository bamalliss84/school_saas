from datetime import date

from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from .models import AcademicTerm, AcademicYear, School, SchoolMembership


User = get_user_model()


class AcademicPeriodManagementTests(APITestCase):
    def setUp(self):
        self.school_a = School.objects.create(name='School A', code='R1A')
        self.school_b = School.objects.create(name='School B', code='R1B')
        self.year_a = AcademicYear.objects.create(
            school=self.school_a,
            name='2026-2027',
            start_date=date(2026, 9, 1),
            end_date=date(2027, 6, 30),
            is_active=True,
        )
        self.year_b = AcademicYear.objects.create(
            school=self.school_b,
            name='2026-2027',
            start_date=date(2026, 9, 1),
            end_date=date(2027, 6, 30),
            is_active=True,
        )
        self.admin = self._make_user('period_admin', 'school_admin', self.school_a)
        self.admin_membership = SchoolMembership.objects.create(
            user=self.admin,
            school=self.school_a,
            role='school_admin',
            status='active',
            is_default=True,
        )
        self.historical_admin = self._make_user('period_history', 'school_admin', self.school_a)
        self.historical_membership = SchoolMembership.objects.create(
            user=self.historical_admin,
            school=self.school_a,
            role='school_admin',
            status='historical',
        )
        self.teacher = self._make_user('period_teacher', 'teacher', self.school_a)
        self.teacher_membership = SchoolMembership.objects.create(
            user=self.teacher,
            school=self.school_a,
            role='teacher',
            status='active',
            is_default=True,
        )

    def _make_user(self, username, role, school):
        return User.objects.create_user(
            username=username,
            password='password123',
            role=role,
            school=school,
            is_active_school_user=True,
        )

    def _login(self, user, membership):
        response = self.client.post(
            '/api/v1/auth/login/',
            {'username': user.username, 'password': 'password123'},
        )
        self.assertEqual(response.status_code, 200, response.data)
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {response.data['access']}",
            HTTP_X_SCHOOL_MEMBERSHIP_ID=str(membership.pk),
        )

    def test_academic_year_management_is_school_scoped_and_does_not_enforce_single_active(self):
        self._login(self.admin, self.admin_membership)

        listed = self.client.get('/api/v1/academic-years/')
        self.assertEqual(listed.status_code, 200, listed.data)
        self.assertEqual([item['id'] for item in listed.data['results']], [self.year_a.id])

        created = self.client.post('/api/v1/academic-years/', {
            'school': self.school_b.id,
            'name': '2027-2028',
            'start_date': '2027-09-01',
            'end_date': '2028-06-30',
            'is_active': True,
        })
        self.assertEqual(created.status_code, 201, created.data)
        self.assertEqual(created.data['school']['id'], self.school_a.id)
        self.assertTrue(AcademicYear.objects.get(pk=created.data['id']).is_active)
        self.assertTrue(AcademicYear.objects.get(pk=self.year_a.id).is_active)

        updated = self.client.patch(
            f"/api/v1/academic-years/{created.data['id']}/",
            {'name': '2027/2028', 'is_active': False},
        )
        self.assertEqual(updated.status_code, 200, updated.data)
        self.assertEqual(updated.data['name'], '2027/2028')
        self.assertFalse(updated.data['is_active'])
        self.assertEqual(self.client.get(f'/api/v1/academic-years/{self.year_b.id}/').status_code, 404)
        self.assertEqual(self.client.delete(f'/api/v1/academic-years/{self.year_a.id}/').status_code, 405)

    def test_academic_year_validation_and_write_guards(self):
        self._login(self.admin, self.admin_membership)
        invalid = self.client.post('/api/v1/academic-years/', {
            'name': 'Invalid',
            'start_date': '2027-06-30',
            'end_date': '2026-09-01',
        })
        self.assertEqual(invalid.status_code, 400)

        AcademicTerm.objects.create(
            school=self.school_a,
            academic_year=self.year_a,
            name='Existing term',
            term_type='term_1',
            start_date=date(2026, 9, 1),
            end_date=date(2026, 12, 15),
        )
        excludes_existing_term = self.client.patch(
            f'/api/v1/academic-years/{self.year_a.id}/',
            {'start_date': '2026-10-01'},
        )
        self.assertEqual(excludes_existing_term.status_code, 400)
        self.assertIn(
            'start_date',
            excludes_existing_term.data.get('errors', excludes_existing_term.data),
        )

        self._login(self.historical_admin, self.historical_membership)
        self.assertEqual(self.client.get('/api/v1/academic-years/').status_code, 200)
        self.assertEqual(self.client.post('/api/v1/academic-years/', {
            'name': 'Blocked', 'start_date': '2027-01-01', 'end_date': '2027-12-31',
        }).status_code, 403)

        self._login(self.teacher, self.teacher_membership)
        self.assertEqual(self.client.get('/api/v1/academic-years/').status_code, 403)

    def test_academic_term_management_filters_and_rejects_cross_school_year(self):
        existing = AcademicTerm.objects.create(
            school=self.school_a,
            academic_year=self.year_a,
            name='Term 1',
            term_type='term_1',
            start_date=date(2026, 9, 1),
            end_date=date(2026, 12, 15),
        )
        AcademicTerm.objects.create(
            school=self.school_b,
            academic_year=self.year_b,
            name='Other term',
            term_type='term_1',
            start_date=date(2026, 9, 1),
            end_date=date(2026, 12, 15),
        )
        self._login(self.admin, self.admin_membership)

        listed = self.client.get('/api/v1/academic-terms/', {'academic_year_id': self.year_a.id})
        self.assertEqual(listed.status_code, 200, listed.data)
        self.assertEqual([item['id'] for item in listed.data['results']], [existing.id])

        foreign = self.client.post('/api/v1/academic-terms/', {
            'academic_year': self.year_b.id,
            'name': 'Foreign',
            'term_type': 'term_2',
            'start_date': '2027-01-01',
            'end_date': '2027-03-31',
        })
        self.assertEqual(foreign.status_code, 400)
        self.assertIn('academic_year', foreign.data.get('errors', foreign.data))

        created = self.client.post('/api/v1/academic-terms/', {
            'school': self.school_b.id,
            'academic_year': self.year_a.id,
            'name': 'Term 2',
            'term_type': 'term_2',
            'start_date': '2026-12-16',
            'end_date': '2027-03-31',
            'is_active': True,
        })
        self.assertEqual(created.status_code, 201, created.data)
        self.assertEqual(created.data['school']['id'], self.school_a.id)

        updated = self.client.patch(
            f"/api/v1/academic-terms/{created.data['id']}/",
            {'name': 'Second Term', 'is_active': False},
        )
        self.assertEqual(updated.status_code, 200, updated.data)
        self.assertEqual(updated.data['name'], 'Second Term')
        self.assertFalse(updated.data['is_active'])
        self.assertEqual(self.client.delete(f"/api/v1/academic-terms/{created.data['id']}/").status_code, 405)

    def test_academic_term_date_overlap_and_duplicate_type_validation(self):
        AcademicTerm.objects.create(
            school=self.school_a,
            academic_year=self.year_a,
            name='Term 1',
            term_type='term_1',
            start_date=date(2026, 9, 1),
            end_date=date(2026, 12, 15),
        )
        self._login(self.admin, self.admin_membership)

        cases = [
            ({'term_type': 'term_2', 'start_date': '2026-12-15', 'end_date': '2027-02-01'}, 'overlap'),
            ({'term_type': 'term_2', 'start_date': '2026-11-01', 'end_date': '2027-02-01'}, 'overlap'),
            ({'term_type': 'term_2', 'start_date': '2026-08-01', 'end_date': '2026-08-31'}, 'start_date'),
            ({'term_type': 'term_2', 'start_date': '2027-02-01', 'end_date': '2027-01-01'}, 'start_date'),
            ({'term_type': 'term_1', 'start_date': '2026-12-16', 'end_date': '2027-02-01'}, 'term_type'),
        ]
        for index, (values, expected_key) in enumerate(cases):
            with self.subTest(index=index):
                response = self.client.post('/api/v1/academic-terms/', {
                    'academic_year': self.year_a.id,
                    'name': f'Candidate {index}',
                    **values,
                })
                self.assertEqual(response.status_code, 400, response.data)
                errors = response.data.get('errors', response.data)
                self.assertTrue(expected_key in errors or expected_key in str(errors).lower(), errors)

        adjacent = self.client.post('/api/v1/academic-terms/', {
            'academic_year': self.year_a.id,
            'name': 'Term 2',
            'term_type': 'term_2',
            'start_date': '2026-12-16',
            'end_date': '2027-02-01',
        })
        self.assertEqual(adjacent.status_code, 201, adjacent.data)

    def test_academic_term_historical_role_and_tenant_guards(self):
        term_b = AcademicTerm.objects.create(
            school=self.school_b,
            academic_year=self.year_b,
            name='Other term',
            term_type='term_1',
            start_date=date(2026, 9, 1),
            end_date=date(2026, 12, 15),
        )
        self._login(self.admin, self.admin_membership)
        self.assertEqual(self.client.get(f'/api/v1/academic-terms/{term_b.id}/').status_code, 404)

        self._login(self.historical_admin, self.historical_membership)
        self.assertEqual(self.client.get('/api/v1/academic-terms/').status_code, 200)
        self.assertEqual(self.client.post('/api/v1/academic-terms/', {
            'academic_year': self.year_a.id,
            'name': 'Blocked',
            'term_type': 'term_2',
            'start_date': '2026-12-16',
            'end_date': '2027-03-01',
        }).status_code, 403)

        self._login(self.teacher, self.teacher_membership)
        self.assertEqual(self.client.get('/api/v1/academic-terms/').status_code, 403)
