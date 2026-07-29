from datetime import date
from unittest.mock import patch

from django.contrib import admin
from django.contrib.auth.models import Permission
from django.core.cache import cache
from django.test import RequestFactory, override_settings
from rest_framework.test import APIClient, APITestCase

from .admin import (
    AcademicYearAdmin,
    ExamResultLogAdmin,
    SchoolAdmin,
    StudentAdmin,
)
from .models import (
    AcademicTerm,
    AcademicYear,
    Attendance,
    Classroom,
    ExamResultLog,
    School,
    Section,
    Student,
    StudentEnrollment,
    User,
)


class SprintTwoPointFiveInfrastructureTests(APITestCase):
    password = 'Infrastructure-test-password-123'

    @classmethod
    def setUpTestData(cls):
        cls.school_a = School.objects.create(name='Infra A', code='IFA')
        cls.school_b = School.objects.create(name='Infra B', code='IFB')
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
        cls.term_a = AcademicTerm.objects.create(
            school=cls.school_a,
            academic_year=cls.year_a,
            name='Term A',
            term_type='term_1',
            start_date=date(2026, 1, 1),
            end_date=date(2026, 12, 31),
        )
        cls.class_a = Classroom.objects.create(
            school=cls.school_a,
            academic_year=cls.year_a,
            name='Grade A',
            code='GA',
        )
        cls.section_a = Section.objects.create(
            school=cls.school_a,
            academic_year=cls.year_a,
            classroom=cls.class_a,
            name='A',
            code='A',
        )
        cls.admin_a = User.objects.create_user(
            username='infra-admin',
            password=cls.password,
            role='school_admin',
            school=cls.school_a,
            academic_year=cls.year_a,
            is_staff=True,
        )
        cls.super_admin = User.objects.create_user(
            username='infra-super',
            password=cls.password,
            role='super_admin',
            is_staff=True,
            is_superuser=True,
        )
        cls.admin_a.user_permissions.add(
            Permission.objects.get(codename='view_school'),
        )
        cls.non_admin_staff = [
            User.objects.create_user(
                username=f'infra-{role}',
                password=cls.password,
                role=role,
                school=cls.school_a,
                is_staff=True,
            )
            for role in ('teacher', 'parent', 'student')
        ]
        cls.student_a = Student.objects.create(
            school=cls.school_a,
            full_name='Ahmed Filter',
            student_code='IFA-S90001',
            gender='male',
        )
        cls.student_b = Student.objects.create(
            school=cls.school_b,
            full_name='Outside Tenant',
            student_code='IFB-S90001',
            gender='female',
        )
        cls.enrollment_a = StudentEnrollment.objects.create(
            student=cls.student_a,
            school=cls.school_a,
            academic_year=cls.year_a,
            classroom=cls.class_a,
            section=cls.section_a,
            status='active',
            is_current=True,
        )
        cls.attendance = Attendance.objects.create(
            student_enrollment=cls.enrollment_a,
            academic_term=cls.term_a,
            attendance_date=date(2026, 7, 20),
            status='present',
        )

    def authenticate(self, user=None):
        self.client.force_authenticate(user=user or self.admin_a)

    def test_01_liveness_returns_200(self):
        response = self.client.get('/health/live/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['status'], 'ok')

    def test_02_readiness_returns_200(self):
        response = self.client.get('/health/ready/')
        self.assertEqual(response.status_code, 200)

    def test_03_readiness_returns_503_on_database_failure(self):
        with patch('core.health.connection.cursor', side_effect=RuntimeError):
            response = self.client.get('/health/ready/')
        self.assertEqual(response.status_code, 503)
        self.assertNotIn('database', str(response.data).lower())

    def test_04_openapi_schema_works(self):
        self.authenticate()
        response = self.client.get('/api/schema/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'openapi:', response.content)

    def test_05_swagger_works_in_development(self):
        self.authenticate()
        response = self.client.get('/api/docs/')
        self.assertEqual(response.status_code, 200)

    def test_06_versioned_me_works(self):
        self.authenticate()
        response = self.client.get('/api/v1/auth/me/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['id'], self.admin_a.id)

    def test_07_legacy_me_still_works(self):
        self.authenticate()
        response = self.client.get('/api/auth/me/')
        self.assertEqual(response.status_code, 200)

    def test_08_student_search_filter_works(self):
        self.authenticate()
        response = self.client.get('/api/v1/students/', {'search': 'Ahmed'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['results'][0]['id'], self.student_a.id)

    def test_09_invalid_student_filter_is_formatted(self):
        self.authenticate()
        response = self.client.get('/api/v1/students/', {'is_active': 'invalid'})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['message'], 'Validation failed.')

    def test_10_school_filter_cannot_escape_tenant(self):
        self.authenticate()
        response = self.client.get(
            '/api/v1/students/',
            {'school_id': self.school_b.id},
        )
        self.assertEqual(response.status_code, 400)

    def test_11_attendance_date_range_works(self):
        self.authenticate()
        response = self.client.get('/api/v1/attendance/', {
            'date_from': '2026-07-01',
            'date_to': '2026-07-31',
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 1)

    def test_12_invalid_attendance_date_range_is_400(self):
        self.authenticate()
        response = self.client.get('/api/v1/attendance/', {
            'date_from': '2026-08-01',
            'date_to': '2026-07-01',
        })
        self.assertEqual(response.status_code, 400)

    def test_13_daily_query_validation_is_formatted(self):
        self.authenticate()
        response = self.client.get('/api/v1/attendance/daily/', {
            'date': 'not-a-date',
        })
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['message'], 'Validation failed.')

    def test_14_method_not_allowed_is_formatted(self):
        response = self.client.post('/health/live/')
        self.assertEqual(response.status_code, 405)
        self.assertEqual(response.data['message'], 'Method not allowed.')

    def test_15_unsupported_media_type_is_formatted(self):
        response = self.client.post(
            '/api/auth/login/',
            '<login />',
            content_type='application/xml',
        )
        self.assertEqual(response.status_code, 415)
        self.assertEqual(response.data['message'], 'Unsupported media type.')

    @override_settings(REST_FRAMEWORK={
        'DEFAULT_AUTHENTICATION_CLASSES': (
            'rest_framework_simplejwt.authentication.JWTAuthentication',
        ),
        'DEFAULT_THROTTLE_CLASSES': (
            'rest_framework.throttling.ScopedRateThrottle',
        ),
        'DEFAULT_THROTTLE_RATES': {'login': '1/minute'},
        'EXCEPTION_HANDLER': 'core.api_exceptions.api_exception_handler',
    })
    def test_16_throttle_429_is_formatted(self):
        from rest_framework.throttling import ScopedRateThrottle

        from .views import LoginTokenObtainPairView

        cache.clear()
        payload = {'username': 'missing', 'password': 'missing'}
        with (
            patch.object(
                LoginTokenObtainPairView,
                'throttle_classes',
                [ScopedRateThrottle],
            ),
            patch.object(
                ScopedRateThrottle,
                'THROTTLE_RATES',
                {'login': '1/minute'},
            ),
        ):
            self.client.post('/api/auth/login/', payload)
            response = self.client.post('/api/auth/login/', payload)
        self.assertEqual(response.status_code, 429)
        self.assertEqual(response.data['message'], 'Request was throttled.')

    def test_17_pagination_metadata_is_backward_compatible(self):
        self.authenticate()
        response = self.client.get('/api/v1/students/')
        for field in (
            'count', 'next', 'previous', 'results',
            'page', 'page_size', 'total_pages',
        ):
            self.assertIn(field, response.data)

    def _admin_request(self, user=None):
        request = RequestFactory().get('/admin/')
        request.user = user or self.admin_a
        return request

    def test_18_admin_anonymous_redirects_to_login(self):
        response = self.client.get('/admin/')
        self.assertRedirects(
            response,
            '/admin/login/?next=/admin/',
            fetch_redirect_response=False,
        )

    def test_19_admin_superuser_opens_index(self):
        self.client.force_login(self.super_admin)
        self.assertEqual(self.client.get('/admin/').status_code, 200)

    def test_20_admin_school_admin_opens_index(self):
        self.client.force_login(self.admin_a)
        self.assertEqual(self.client.get('/admin/').status_code, 200)

    def test_21_admin_non_admin_roles_are_denied_even_if_staff(self):
        for user in self.non_admin_staff:
            with self.subTest(role=user.role):
                self.client.force_login(user)
                response = self.client.get('/admin/')
                self.assertEqual(response.status_code, 302)
                self.assertIn('/admin/login/', response.url)
                self.client.logout()

    def test_22_admin_school_changelist_is_tenant_scoped(self):
        self.client.force_login(self.admin_a)
        response = self.client.get('/admin/core/school/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.school_a.name)
        self.assertNotContains(response, self.school_b.name)

    def test_23_admin_school_admin_sees_only_own_school(self):
        model_admin = SchoolAdmin(School, admin.site)
        queryset = model_admin.get_queryset(self._admin_request())
        self.assertEqual(list(queryset), [self.school_a])

    def test_24_admin_school_admin_cannot_see_other_school(self):
        model_admin = SchoolAdmin(School, admin.site)
        queryset = model_admin.get_queryset(self._admin_request())
        self.assertFalse(queryset.filter(pk=self.school_b.id).exists())

    def test_25_admin_foreign_key_is_tenant_scoped(self):
        model_admin = AcademicYearAdmin(AcademicYear, admin.site)
        field = AcademicYear._meta.get_field('school')
        formfield = model_admin.formfield_for_foreignkey(
            field,
            self._admin_request(),
        )
        self.assertEqual(list(formfield.queryset), [self.school_a])

    def test_26_exam_result_log_admin_is_immutable(self):
        model_admin = ExamResultLogAdmin(ExamResultLog, admin.site)
        request = self._admin_request(self.super_admin)
        self.assertFalse(model_admin.has_add_permission(request))
        self.assertFalse(model_admin.has_change_permission(request))
        self.assertFalse(model_admin.has_delete_permission(request))

    def test_27_student_admin_current_enrollment_avoids_n_plus_one(self):
        model_admin = StudentAdmin(Student, admin.site)
        request = self._admin_request()
        with self.assertNumQueries(2):
            students = list(model_admin.get_queryset(request))
            for student in students:
                model_admin.current_classroom(student)
                model_admin.current_section(student)

    def test_28_local_security_settings_do_not_force_https(self):
        from django.conf import settings

        self.assertFalse(settings.DEBUG)
        self.assertTrue(settings.SECURE_CONTENT_TYPE_NOSNIFF)
        self.assertFalse(settings.SECURE_SSL_REDIRECT)

    def test_29_schema_does_not_expose_secrets(self):
        self.authenticate()
        response = self.client.get('/api/schema/')
        content = response.content.decode('utf-8')
        self.assertNotIn('school_pass_123', content)
        self.assertNotIn('django-insecure-development-only-change-me', content)

    def test_30_versioned_and_legacy_attendance_both_work(self):
        self.authenticate()
        versioned = self.client.get('/api/v1/attendance/')
        legacy = self.client.get('/api/attendance/')
        self.assertEqual(versioned.status_code, 200)
        self.assertEqual(legacy.status_code, 200)
        self.assertEqual(versioned.data['count'], legacy.data['count'])
