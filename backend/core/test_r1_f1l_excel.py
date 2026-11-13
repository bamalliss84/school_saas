"""Release 1.0 F1L-6 — Excel import/export acceptance tests.

Covers Excel templates, parsing an uploaded workbook into the existing
preview -> confirm import, value aliases, leading zeros, formula-injection
neutralisation, upload limits, and operational exports (attendance, results,
timetable, homework) scoped to the active school and academic year.
"""
import io
from datetime import date, datetime, time
from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from openpyxl import Workbook, load_workbook
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from . import test_sprint3_exams
from .context import ensure_legacy_membership
from .models import (
    Attendance, Homework, Parent, SchoolMembership, SchoolPeriod, SchoolTimetableConfig,
    Student, StudentEnrollment, TimetableEntry,
)
from .services import spreadsheets
from .test_r1_f1k_f1n_admin_release import AdminReleaseFixture

XLSX = spreadsheets.XLSX_CONTENT_TYPE


def workbook_upload(rows, name='data.xlsx'):
    book = Workbook()
    sheet = book.active
    for row in rows:
        sheet.append(row)
    buffer = io.BytesIO()
    book.save(buffer)
    return SimpleUploadedFile(name, buffer.getvalue(), content_type=XLSX)


def open_xlsx(response):
    return load_workbook(io.BytesIO(response.content))


class F1LExcelImportTests(AdminReleaseFixture):
    def parse(self, kind, upload, headers=None):
        return self.client.post(
            '/api/v1/admin/data/import/parse/', {'kind': kind, 'file': upload},
            format='multipart', **(headers or self.headers()),
        )

    def test_template_has_arabic_headers_rtl_text_codes_and_instructions(self):
        response = self.client.get('/api/v1/admin/data/template/', {'kind': 'guardians'}, **self.headers())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], XLSX)
        book = open_xlsx(response)
        sheet = book.worksheets[0]
        headers = [cell.value for cell in sheet[1]]
        self.assertEqual(headers[:3], ['كود الطالب', 'اسم ولي الأمر', 'صلة القرابة'])
        self.assertNotIn('كلمة المرور', ' '.join(headers))
        self.assertTrue(sheet.sheet_view.rightToLeft)
        self.assertEqual(sheet['A2'].number_format, '@')
        self.assertEqual(book.sheetnames[1], 'تعليمات')

    def test_template_rejects_unknown_kind_and_non_admin(self):
        self.assertEqual(self.client.get('/api/v1/admin/data/template/', {'kind': 'results'}, **self.headers()).status_code, 400)
        self.assertEqual(self.client.get('/api/v1/admin/data/template/', **self.teacher_context()).status_code, 403)

    def test_student_workbook_flows_through_preview_and_confirm(self):
        upload = workbook_upload([
            ['الاسم الكامل', 'الجنس', 'تاريخ الميلاد'],
            ['سارة أحمد', 'أنثى', datetime(2015, 4, 2)],
            [None, None, None],
            ['خالد علي', 'ذكر', '2014-09-15'],
        ])
        parsed = self.parse('students', upload)
        self.assertEqual(parsed.status_code, 200, parsed.content)
        rows = parsed.data['rows']
        self.assertEqual(rows, [
            {'full_name': 'سارة أحمد', 'gender': 'female', 'birth_date': '2015-04-02'},
            {'full_name': 'خالد علي', 'gender': 'male', 'birth_date': '2014-09-15'},
        ])
        preview = self.client.post('/api/v1/admin/data/import/', {'kind': 'students', 'rows': rows},
                                   format='json', **self.headers())
        self.assertEqual(preview.status_code, 200, preview.content)
        self.assertFalse(Student.objects.filter(school=self.school).exists())
        done = self.client.post('/api/v1/admin/data/import/', {'kind': 'students', 'rows': rows, 'confirm': True},
                                format='json', **self.headers())
        self.assertEqual(done.status_code, 201, done.content)
        self.assertEqual(Student.objects.filter(school=self.school).count(), 2)
        self.assertFalse(Student.objects.filter(school=self.other).exists())

    def test_guardian_phone_keeps_leading_zero_and_arabic_values_map(self):
        classroom, section = self.classroom(self.school, self.year)
        student = Student.objects.create(school=self.school, full_name='Child', student_code='F1K-S9', gender='male')
        StudentEnrollment.objects.create(student=student, school=self.school, academic_year=self.year,
                                         classroom=classroom, section=section)
        upload = workbook_upload([
            ['كود الطالب', 'اسم ولي الأمر', 'صلة القرابة', 'الجوال', 'ولي الأمر الأساسي'],
            ['F1K-S9', 'أحمد', 'أب', '0501234567', 'نعم'],
        ])
        parsed = self.parse('guardians', upload)
        self.assertEqual(parsed.status_code, 200, parsed.content)
        self.assertEqual(parsed.data['rows'][0], {
            'student_code': 'F1K-S9', 'full_name': 'أحمد', 'relationship': 'father',
            'phone': '0501234567', 'is_primary': 'true',
        })
        done = self.client.post('/api/v1/admin/data/import/', {
            'kind': 'guardians', 'rows': parsed.data['rows'], 'confirm': True,
        }, format='json', **self.headers())
        self.assertEqual(done.status_code, 201, done.content)
        self.assertEqual(Parent.objects.get(school=self.school, full_name='أحمد').phone, '0501234567')

    def test_api_field_names_are_accepted_as_headers(self):
        parsed = self.parse('teachers', workbook_upload([['full_name', 'phone'], ['Teacher A', '0555']]))
        self.assertEqual(parsed.status_code, 200, parsed.content)
        self.assertEqual(parsed.data['rows'], [{'full_name': 'Teacher A', 'phone': '0555'}])

    def test_bad_files_and_columns_are_rejected_without_writes(self):
        fake = SimpleUploadedFile('data.xlsx', b'name,gender\nA,male\n', content_type=XLSX)
        self.assertEqual(self.parse('students', fake).status_code, 400)
        unknown = self.parse('students', workbook_upload([['الاسم الكامل', 'الجنس', 'عمود غريب'], ['A', 'ذكر', 'x']]))
        self.assertEqual(unknown.status_code, 400)
        self.assertIn('عمود غريب', unknown.content.decode())
        missing = self.parse('guardians', workbook_upload([['اسم ولي الأمر'], ['A']]))
        self.assertEqual(missing.status_code, 400)
        self.assertIn('كود الطالب', missing.content.decode())
        empty = self.parse('students', workbook_upload([['الاسم الكامل', 'الجنس']]))
        self.assertEqual(empty.status_code, 400)
        self.assertEqual(self.parse('results', workbook_upload([['x'], ['y']])).status_code, 400)
        no_file = self.client.post('/api/v1/admin/data/import/parse/', {'kind': 'students'},
                                   format='multipart', **self.headers())
        self.assertEqual(no_file.status_code, 400)
        self.assertFalse(Student.objects.exists())

    def test_row_and_size_limits(self):
        rows = [['الاسم الكامل', 'الجنس']] + [[f'S{i}', 'ذكر'] for i in range(spreadsheets.MAX_ROWS + 1)]
        self.assertEqual(self.parse('students', workbook_upload(rows)).status_code, 400)
        with patch.object(spreadsheets, 'MAX_UNCOMPRESSED_BYTES', 100):
            response = self.parse('students', workbook_upload([['الاسم الكامل', 'الجنس'], ['A', 'ذكر']]))
        self.assertEqual(response.status_code, 400)
        self.assertIn('uncompressed', response.content.decode())
        with patch.object(spreadsheets, 'MAX_UPLOAD_BYTES', 10):
            self.assertEqual(self.parse('students', workbook_upload([['الاسم الكامل'], ['A']])).status_code, 400)

    def test_historical_and_teacher_contexts_cannot_parse_imports(self):
        upload = workbook_upload([['الاسم الكامل', 'الجنس'], ['A', 'ذكر']])
        self.assertEqual(self.parse('students', upload, self.teacher_context()).status_code, 403)
        self.make_historical()
        upload = workbook_upload([['الاسم الكامل', 'الجنس'], ['A', 'ذكر']])
        self.assertEqual(self.parse('students', upload).status_code, 403)

    def test_xlsx_student_export_neutralises_formulas_and_keeps_codes_as_text(self):
        classroom, section = self.classroom(self.school, self.year)
        student = Student.objects.create(
            school=self.school, full_name='=HYPERLINK("http://x","y")', student_code='0012', gender='male',
        )
        StudentEnrollment.objects.create(student=student, school=self.school, academic_year=self.year,
                                         classroom=classroom, section=section)
        response = self.client.get('/api/v1/admin/data/export/', {'kind': 'students', 'output': 'xlsx'}, **self.headers())
        self.assertEqual(response.status_code, 200)
        self.assertIn('attachment', response['Content-Disposition'])
        sheet = open_xlsx(response).worksheets[0]
        self.assertEqual(sheet['A1'].value, 'كود الطالب')
        self.assertEqual(sheet['A2'].value, '0012')
        self.assertEqual(sheet['A2'].number_format, '@')
        self.assertTrue(str(sheet['B2'].value).startswith("'="))

    def test_unknown_output_is_rejected_and_json_contract_is_unchanged(self):
        self.assertEqual(self.client.get('/api/v1/admin/data/export/', {'output': 'pdf'}, **self.headers()).status_code, 400)
        response = self.client.get('/api/v1/admin/data/export/', {'kind': 'students'}, **self.headers())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(set(response.data), {'kind', 'rows'})


class F1LOperationalExportTests(APITestCase):
    password = test_sprint3_exams.SprintThreeExamPlatformTests.password
    setUpTestData = classmethod(test_sprint3_exams.SprintThreeExamPlatformTests.setUpTestData.__func__)

    def setUp(self):
        self.admin_m = ensure_legacy_membership(self.admin_user)
        self.client.credentials(
            HTTP_AUTHORIZATION=f'Bearer {RefreshToken.for_user(self.admin_user).access_token}',
            HTTP_X_SCHOOL_MEMBERSHIP_ID=str(self.admin_m.pk),
        )

    def export(self, kind, **params):
        return self.client.get('/api/v1/admin/data/export/', {'kind': kind, **params})

    def attendance(self, enrollment, assignment, day, status='present'):
        return Attendance.objects.create(
            student_enrollment=enrollment, teacher_assignment=assignment, academic_term=self.term if enrollment.school_id == self.school.pk else self.other_term,
            attendance_date=day, status=status,
        )

    def test_attendance_export_is_school_scoped_and_filtered(self):
        self.attendance(self.enrollment, self.assignment, date(2026, 3, 10), 'absent')
        self.attendance(self.enrollment_two, self.assignment, date(2026, 3, 12))
        self.attendance(self.other_enrollment, self.other_assignment, date(2026, 3, 10))
        response = self.export('attendance')
        self.assertEqual(response.status_code, 200, response.content)
        codes = sorted(row['student_code'] for row in response.data['rows'])
        self.assertEqual(codes, ['S3A-S90001', 'S3A-S90002'])
        first = next(row for row in response.data['rows'] if row['student_code'] == 'S3A-S90001')
        self.assertEqual((first['status'], first['subject'], first['teacher']), ('غائب', 'Math', 'Teacher One'))
        ranged = self.export('attendance', date_from='2026-03-11', date_to='2026-03-31')
        self.assertEqual([row['student_code'] for row in ranged.data['rows']], ['S3A-S90002'])
        foreign_class = self.export('attendance', classroom_id=self.other_classroom.pk)
        self.assertEqual(foreign_class.data['rows'], [])

    def test_attendance_filters_are_validated(self):
        self.assertEqual(self.export('attendance', date_from='bad').status_code, 400)
        self.assertEqual(self.export('attendance', date_from='2026-04-01', date_to='2026-03-01').status_code, 400)
        self.assertEqual(self.export('attendance', classroom_id='x').status_code, 400)

    def test_results_export_xlsx_is_school_scoped(self):
        response = self.export('results', output='xlsx')
        self.assertEqual(response.status_code, 200)
        sheet = open_xlsx(response).worksheets[0]
        self.assertEqual(sheet.title, 'النتائج')
        values = [[cell.value for cell in row] for row in sheet.iter_rows(min_row=2)]
        self.assertEqual(len(values), 1)
        self.assertIn('Math Midterm', values[0])
        self.assertNotIn('Other Math Midterm', [v for row in values for v in row])

    def test_timetable_and_homework_exports_are_school_scoped(self):
        SchoolTimetableConfig.objects.get_or_create(
            school=self.school, academic_year=self.year, defaults={'working_days': [0, 1, 2, 3, 4]},
        )
        period = SchoolPeriod.objects.create(
            school=self.school, academic_year=self.year, name='P1', sequence=1,
            start_time=time(8, 0), end_time=time(8, 45),
        )
        TimetableEntry.objects.create(
            school=self.school, academic_year=self.year, teacher_assignment=self.assignment, weekday=0, period=period,
        )
        Homework.objects.create(
            school=self.school, academic_year=self.year, academic_term=self.term, teacher_assignment=self.assignment,
            title='Fractions', due_date=timezone.make_aware(datetime(2026, 3, 20, 10, 0)), created_by=self.teacher_user,
        )
        Homework.objects.create(
            school=self.other_school, academic_year=self.other_year, academic_term=self.other_term,
            teacher_assignment=self.other_assignment, title='Foreign',
            due_date=timezone.make_aware(datetime(2026, 3, 20, 10, 0)), created_by=self.other_teacher_user,
        )
        timetable = self.export('timetable')
        self.assertEqual(timetable.status_code, 200, timetable.content)
        self.assertEqual([(r['weekday'], r['period'], r['start_time']) for r in timetable.data['rows']], [('الأحد', 'P1', '08:00')])
        homework = self.export('homework', output='xlsx')
        self.assertEqual(homework.status_code, 200)
        titles = [row[0].value for row in open_xlsx(homework).worksheets[0].iter_rows(min_row=2)]
        self.assertEqual(titles, ['Fractions'])

    def test_historical_admin_can_export_and_others_cannot(self):
        SchoolMembership.objects.filter(pk=self.admin_m.pk).update(status='historical', is_default=False)
        self.assertEqual(self.export('results').status_code, 200)
        teacher_m = ensure_legacy_membership(self.teacher_user)
        self.client.credentials(
            HTTP_AUTHORIZATION=f'Bearer {RefreshToken.for_user(self.teacher_user).access_token}',
            HTTP_X_SCHOOL_MEMBERSHIP_ID=str(teacher_m.pk),
        )
        self.assertEqual(self.export('attendance').status_code, 403)

    def test_export_row_cap_asks_to_narrow_filters(self):
        self.attendance(self.enrollment, self.assignment, date(2026, 3, 10))
        with patch('core.services.data_exchange.MAX_EXPORT_ROWS', 0):
            response = self.export('attendance')
        self.assertEqual(response.status_code, 400)

