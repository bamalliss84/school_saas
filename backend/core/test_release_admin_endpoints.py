from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from core.models import AcademicYear, School, SchoolMembership, User


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
        response = self.client.patch(
            '/api/v1/admin/settings/', {'phone': '1'}, format='json', **self.headers,
        )
        self.assertEqual(response.status_code, 403)
        response = self.client.post(
            '/api/v1/admin/data/import/', {'kind': 'students', 'rows': []},
            format='json', **self.headers,
        )
        self.assertEqual(response.status_code, 403)
