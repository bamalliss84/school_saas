from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from core.models import AcademicYear, SchoolSetting, School, SchoolMembership, User


class ReleaseAdminEndpointsTests(TestCase):
    def setUp(self):
        self.school = School.objects.create(name='Release School', code='REL')
        self.year = AcademicYear.objects.create(
            school=self.school, name='2026/2027', start_date='2026-08-01',
            end_date='2027-06-30', is_active=True,
        )
        self.user = User.objects.create_user(
            username='release-admin', password='pass1234', school=self.school,
            academic_year=self.year, role='school_admin',
        )
        self.membership = SchoolMembership.objects.create(
            user=self.user, school=self.school, role='school_admin', status='active',
            is_default=True,
        )
        self.client = APIClient()
        access = str(RefreshToken.for_user(self.user).access_token)
        self.headers = {'HTTP_AUTHORIZATION': f'Bearer {access}', 'HTTP_X_SCHOOL_MEMBERSHIP_ID': str(self.membership.id)}

    def test_settings_are_tenant_scoped_and_writable(self):
        response = self.client.get('/api/v1/admin/settings/', **self.headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['school']['id'], self.school.id)
        response = self.client.patch(
            '/api/v1/admin/settings/', {'phone': '0500000000', 'school_name_ar': 'مدرسة الإصدار'},
            format='json', **self.headers,
        )
        self.assertEqual(response.status_code, 200)
        self.school.refresh_from_db()
        self.assertEqual(self.school.phone, '0500000000')

    def test_onboarding_and_reports_do_not_escape_school(self):
        other = School.objects.create(name='Other', code='OTHER')
        User.objects.create_user(username='other-admin', password='x', school=other, role='school_admin')
        response = self.client.get('/api/v1/admin/onboarding/status/', **self.headers)
        self.assertEqual(response.status_code, 200)
        self.assertIn('steps', response.data)
        response = self.client.get('/api/v1/admin/reports/summary/', **self.headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['students']['total'], 0)

    def test_historical_context_blocks_release_writes(self):
        self.membership.status = 'historical'
        self.membership.is_default = False
        self.membership.save()
        access = str(RefreshToken.for_user(self.user).access_token)
        self.headers = {'HTTP_AUTHORIZATION': f'Bearer {access}', 'HTTP_X_SCHOOL_MEMBERSHIP_ID': str(self.membership.id)}
        response = self.client.patch(
            '/api/v1/admin/settings/', {'phone': '1'}, format='json', **self.headers,
        )
        self.assertEqual(response.status_code, 403)
        response = self.client.post(
            '/api/v1/admin/data/import/', {'kind': 'students', 'rows': []},
            format='json', **self.headers,
        )
        self.assertEqual(response.status_code, 403)


    def test_historical_settings_get_does_not_create_settings(self):
        SchoolSetting.objects.filter(school=self.school).delete()
        self.membership.status = 'historical'
        self.membership.is_default = False
        self.membership.save()
        access = str(RefreshToken.for_user(self.user).access_token)
        headers = {'HTTP_AUTHORIZATION': f'Bearer {access}', 'HTTP_X_SCHOOL_MEMBERSHIP_ID': str(self.membership.id)}
        response = self.client.get('/api/v1/admin/settings/', **headers)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(SchoolSetting.objects.filter(school=self.school).exists())


    def test_import_requires_explicit_confirmation_after_preview(self):
        payload = {'kind': 'teachers', 'rows': [{
            'employee_code': 'IMP-1', 'full_name': 'Imported Teacher',
            'phone': '0501111111', 'email': 'imported@example.com',
            'specialization': 'Math', 'is_active': True,
        }]}
        preview = self.client.post('/api/v1/admin/data/import/', payload, format='json', **self.headers)
        self.assertEqual(preview.status_code, 200)
        self.assertTrue(preview.data['valid'])
        self.assertFalse(preview.data['confirmed'])
        self.assertEqual(preview.data['created'], 0)

        payload['confirm'] = True
        confirmed = self.client.post('/api/v1/admin/data/import/', payload, format='json', **self.headers)
        self.assertEqual(confirmed.status_code, 201)
        self.assertTrue(confirmed.data['confirmed'])
        self.assertEqual(confirmed.data['created'], 1)

    def test_reports_support_operational_filters(self):
        response = self.client.get(
            '/api/v1/admin/reports/summary/?date_from=2026-08-01&date_to=2026-08-31',
            **self.headers,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['filters']['date_from'], '2026-08-01')
        self.assertIn('completion_rate', response.data['homework'])

    def test_guardian_import_preview_is_non_mutating(self):
        payload = {'kind': 'guardians', 'rows': [{
            'student_code': 'MISSING', 'full_name': 'Guardian',
            'relationship': 'father',
        }]}
        response = self.client.post('/api/v1/admin/data/import/', payload, format='json', **self.headers)
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.data['valid'])

    def test_student_export_uses_import_compatible_identity_keys(self):
        response = self.client.get('/api/v1/admin/data/export/?kind=students', **self.headers)
        self.assertEqual(response.status_code, 200)
        for row in response.data['rows']:
            self.assertIn('full_name', row)
            self.assertIn('gender', row)
            self.assertNotIn('student__full_name', row)
