"""Release 1.0 acceptance tests for F1K Onboarding, F1L Import/Export,
F1M Reports and F1N Settings (docs/RELEASE1_ADMIN_F1F_F1N.md)."""
import io
import tempfile

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from PIL import Image
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from core.models import (
    AcademicYear, Classroom, School, SchoolMembership, SchoolSetting, Section, Student,
    StudentEnrollment, Teacher, User,
)


class AdminReleaseFixture(TestCase):
    def setUp(self):
        self.school = School.objects.create(name='F1 School', code='F1K')
        self.other = School.objects.create(name='F1 Other', code='F1X')
        self.year = AcademicYear.objects.create(
            school=self.school, name='2026/2027', start_date='2026-08-01',
            end_date='2027-06-30', is_active=True,
        )
        self.other_year = AcademicYear.objects.create(
            school=self.other, name='2026/2027', start_date='2026-08-01',
            end_date='2027-06-30', is_active=True,
        )
        self.admin = User.objects.create_user(
            username='f1k-admin', password='pass1234', school=self.school,
            academic_year=self.year, role='school_admin',
        )
        self.membership = SchoolMembership.objects.create(
            user=self.admin, school=self.school, role='school_admin', status='active', is_default=True,
        )
        self.client = APIClient()

    def headers(self, user=None, membership=None):
        user, membership = user or self.admin, membership or self.membership
        return {
            'HTTP_AUTHORIZATION': f'Bearer {RefreshToken.for_user(user).access_token}',
            'HTTP_X_SCHOOL_MEMBERSHIP_ID': str(membership.id),
        }

    def make_historical(self):
        self.membership.status = 'historical'
        self.membership.is_default = False
        self.membership.save()

    def teacher_context(self):
        user = User.objects.create_user(
            username='f1k-teacher', password='pass1234', school=self.school, role='teacher',
        )
        membership = SchoolMembership.objects.create(
            user=user, school=self.school, role='teacher', status='active', is_default=True,
        )
        return self.headers(user, membership)

    def classroom(self, school, year, name='Grade 1'):
        classroom = Classroom.objects.create(school=school, academic_year=year, name=name)
        section = Section.objects.create(school=school, academic_year=year, classroom=classroom, name='A')
        return classroom, section


class F1KOnboardingTests(AdminReleaseFixture):
    def steps(self, headers=None):
        response = self.client.get('/api/v1/admin/onboarding/status/', **(headers or self.headers()))
        self.assertEqual(response.status_code, 200)
        return response.data, {s['key']: s['complete'] for s in response.data['steps']}

    def test_teachers_step_is_independent_from_assignments(self):
        _, steps = self.steps()
        self.assertFalse(steps['teachers'])
        Teacher.objects.create(
            school=self.school, academic_year=self.year, full_name='Unassigned', employee_code='F1K-T1',
        )
        data, steps = self.steps()
        self.assertTrue(steps['teachers'])
        self.assertFalse(steps['assignments'])
        self.assertEqual(data['completed'], sum(1 for v in steps.values() if v))
        self.assertEqual(data['progress'], round(data['completed'] * 100 / data['total']))

    def test_other_school_setup_does_not_count(self):
        Teacher.objects.create(
            school=self.other, academic_year=self.other_year, full_name='Foreign', employee_code='F1X-T1',
        )
        self.classroom(self.other, self.other_year)
        _, steps = self.steps()
        self.assertFalse(steps['teachers'])
        self.assertFalse(steps['classes'])
        self.assertFalse(steps['sections'])

    def test_teacher_cannot_read_onboarding(self):
        response = self.client.get('/api/v1/admin/onboarding/status/', **self.teacher_context())
        self.assertEqual(response.status_code, 403)

    def test_historical_admin_can_read_onboarding(self):
        self.make_historical()
        self.steps(self.headers())


class F1LImportExportTests(AdminReleaseFixture):
    def test_invalid_rows_are_reported_per_row_and_nothing_is_imported(self):
        rows = [
            {'employee_code': 'F1L-1', 'full_name': 'Valid Teacher'},
            {'employee_code': '', 'full_name': ''},
        ]
        response = self.client.post(
            '/api/v1/admin/data/import/', {'kind': 'teachers', 'rows': rows, 'confirm': True},
            format='json', **self.headers(),
        )
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.data['valid'])
        self.assertEqual([e['row'] for e in response.data['errors']], [3])
        self.assertFalse(Teacher.objects.filter(employee_code='F1L-1').exists())

    def test_guardian_import_cannot_reference_foreign_school_student(self):
        foreign = Student.objects.create(school=self.other, full_name='Foreign', student_code='F1X-S1', gender='male')
        response = self.client.post('/api/v1/admin/data/import/', {'kind': 'guardians', 'rows': [
            {'student_code': foreign.student_code, 'full_name': 'Guardian', 'relationship': 'father'},
        ]}, format='json', **self.headers())
        self.assertEqual(response.status_code, 400)
        self.assertIn('student_code', response.data['errors'][0]['errors'])

    def test_export_is_school_scoped_and_allowed_in_historical_context(self):
        classroom, section = self.classroom(self.school, self.year)
        other_classroom, other_section = self.classroom(self.other, self.other_year)
        mine = Student.objects.create(school=self.school, full_name='Mine', student_code='F1K-S1', gender='male')
        theirs = Student.objects.create(school=self.other, full_name='Theirs', student_code='F1X-S2', gender='male')
        StudentEnrollment.objects.create(student=mine, school=self.school, academic_year=self.year,
                                         classroom=classroom, section=section)
        StudentEnrollment.objects.create(student=theirs, school=self.other, academic_year=self.other_year,
                                         classroom=other_classroom, section=other_section)
        self.make_historical()
        response = self.client.get('/api/v1/admin/data/export/?kind=students', **self.headers())
        self.assertEqual(response.status_code, 200)
        self.assertEqual([r['student_code'] for r in response.data['rows']], ['F1K-S1'])

    def test_unknown_export_kind_and_teacher_role_are_rejected(self):
        self.assertEqual(self.client.get('/api/v1/admin/data/export/?kind=grades', **self.headers()).status_code, 400)
        self.assertEqual(self.client.get('/api/v1/admin/data/export/', **self.teacher_context()).status_code, 403)

    def test_import_row_limit_is_enforced(self):
        rows = [{'employee_code': f'L{i}', 'full_name': 'T'} for i in range(1001)]
        response = self.client.post('/api/v1/admin/data/import/', {'kind': 'teachers', 'rows': rows},
                                    format='json', **self.headers())
        self.assertEqual(response.status_code, 400)


class F1MReportsTests(AdminReleaseFixture):
    url = '/api/v1/admin/reports/summary/'

    def test_malformed_filters_return_400_not_500(self):
        for query in ('classroom_id=abc', 'section_id=1.5', 'student_id=x', 'date_from=2026-13-40',
                      'date_to=yesterday', 'date_from=2026-09-10&date_to=2026-09-01'):
            with self.subTest(query=query):
                response = self.client.get(f'{self.url}?{query}', **self.headers())
                self.assertEqual(response.status_code, 400)

    def test_foreign_classroom_filter_returns_no_foreign_data(self):
        other_classroom, other_section = self.classroom(self.other, self.other_year)
        theirs = Student.objects.create(school=self.other, full_name='Theirs', student_code='F1X-S3', gender='male')
        StudentEnrollment.objects.create(student=theirs, school=self.other, academic_year=self.other_year,
                                         classroom=other_classroom, section=other_section)
        response = self.client.get(f'{self.url}?classroom_id={other_classroom.pk}', **self.headers())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['students']['total'], 0)
        self.assertEqual(response.data['filters']['classroom_id'], str(other_classroom.pk))

    def test_teacher_cannot_read_admin_reports(self):
        self.assertEqual(self.client.get(self.url, **self.teacher_context()).status_code, 403)


class F1NSettingsTests(AdminReleaseFixture):
    url = '/api/v1/admin/settings/'

    def test_profile_and_preferences_update(self):
        response = self.client.patch(self.url, {
            'name': 'F1 School Renamed', 'phone': '0500000000', 'school_name_en': 'F1 School',
            'primary_color': '#123456', 'language': 'en', 'allow_parent_notifications': False,
        }, format='json', **self.headers())
        self.assertEqual(response.status_code, 200, response.data)
        self.school.refresh_from_db()
        self.assertEqual(self.school.name, 'F1 School Renamed')
        setting = SchoolSetting.objects.get(school=self.school)
        self.assertEqual((setting.primary_color, setting.language, setting.allow_parent_notifications),
                         ('#123456', 'en', False))

    def test_invalid_language_and_color_are_rejected(self):
        for payload in ({'language': 'fr'}, {'primary_color': 'red'}):
            with self.subTest(payload=payload):
                self.assertEqual(
                    self.client.patch(self.url, payload, format='json', **self.headers()).status_code, 400,
                )

    def test_settings_never_touch_another_school(self):
        self.client.patch(self.url, {'name': 'Changed'}, format='json', **self.headers())
        self.other.refresh_from_db()
        self.assertEqual(self.other.name, 'F1 Other')
        self.assertFalse(SchoolSetting.objects.filter(school=self.other).exists())

    def test_teacher_cannot_read_or_write_settings(self):
        headers = self.teacher_context()
        self.assertEqual(self.client.get(self.url, **headers).status_code, 403)
        self.assertEqual(self.client.patch(self.url, {'name': 'x'}, format='json', **headers).status_code, 403)


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class F1NLogoTests(AdminReleaseFixture):
    url = '/api/v1/admin/settings/logo/'

    def image(self, fmt='PNG', name='logo.png', size=(8, 8)):
        buffer = io.BytesIO()
        Image.new('RGB', size, (20, 90, 160)).save(buffer, format=fmt)
        return SimpleUploadedFile(name, buffer.getvalue(), content_type=f'image/{fmt.lower()}')

    def upload(self, file, headers=None):
        return self.client.post(self.url, {'logo': file}, format='multipart', **(headers or self.headers()))

    def test_upload_replace_read_and_remove_logo(self):
        first = self.upload(self.image())
        self.assertEqual(first.status_code, 200, first.data)
        self.assertTrue(first.data['logo_url'].endswith('.png'))
        setting = SchoolSetting.objects.get(school=self.school)
        old_name = setting.logo.name
        with self.captureOnCommitCallbacks(execute=True):
            second = self.upload(self.image('JPEG', 'logo.jpg'))
        self.assertEqual(second.status_code, 200)
        setting.refresh_from_db()
        self.assertTrue(setting.logo.name.endswith('.jpg'))
        self.assertFalse(setting.logo.storage.exists(old_name))
        read = self.client.get('/api/v1/admin/settings/', **self.headers())
        self.assertEqual(read.data['settings']['logo_url'], second.data['logo_url'])
        with self.captureOnCommitCallbacks(execute=True):
            removed = self.client.delete(self.url, **self.headers())
        self.assertEqual(removed.status_code, 204)
        setting.refresh_from_db()
        self.assertFalse(setting.logo)
        self.assertIsNone(self.client.get('/api/v1/admin/settings/', **self.headers()).data['settings']['logo_url'])

    def test_rejects_svg_fake_images_oversize_and_missing_file(self):
        svg = SimpleUploadedFile('logo.svg', b'<svg xmlns="http://www.w3.org/2000/svg"><script>x</script></svg>',
                                 content_type='image/svg+xml')
        fake = SimpleUploadedFile('logo.png', b'not really a png', content_type='image/png')
        gif = self.image('GIF', 'logo.gif')
        for file in (svg, fake, gif):
            with self.subTest(name=file.name):
                self.assertEqual(self.upload(file).status_code, 400)
        big = SimpleUploadedFile('big.png', b'0' * (2 * 1024 * 1024 + 1), content_type='image/png')
        self.assertEqual(self.upload(big).status_code, 400)
        self.assertEqual(self.client.post(self.url, {}, format='multipart', **self.headers()).status_code, 400)
        self.assertFalse(SchoolSetting.objects.filter(school=self.school).exclude(logo='').exclude(logo=None).exists())

    def test_historical_and_teacher_contexts_cannot_change_logo(self):
        self.assertEqual(self.upload(self.image(), self.teacher_context()).status_code, 403)
        self.make_historical()
        self.assertEqual(self.upload(self.image()).status_code, 403)
        self.assertEqual(self.client.delete(self.url, **self.headers()).status_code, 403)
        self.assertFalse(SchoolSetting.objects.filter(school=self.school).exists())
