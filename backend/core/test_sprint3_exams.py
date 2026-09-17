from datetime import date
from decimal import Decimal

from django.contrib import admin
from django.db import connection
from django.test import RequestFactory
from django.utils import timezone
from django.test.utils import CaptureQueriesContext
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from .admin import ExamResultAdmin, ExamResultLogAdmin
from .models import (
    AcademicTerm, AcademicYear, Classroom, Exam, ExamResult, ExamResultLog,
    ExamType, Parent, School, Section, Student, StudentEnrollment,
    StudentGuardian, Subject, Teacher, TeacherAssignment, User,
)
from .context import ensure_legacy_membership


class SprintThreeExamPlatformTests(APITestCase):
    password = 'Sprint3-test-password-123'

    @classmethod
    def setUpTestData(cls):
        cls.school = School.objects.create(name='Sprint 3 School', code='S3A')
        cls.other_school = School.objects.create(name='Other School', code='S3B')
        cls.year = AcademicYear.objects.create(
            school=cls.school, name='2026', start_date=date(2026, 1, 1),
            end_date=date(2026, 12, 31), is_active=True,
        )
        cls.other_year = AcademicYear.objects.create(
            school=cls.other_school, name='2026', start_date=date(2026, 1, 1),
            end_date=date(2026, 12, 31), is_active=True,
        )
        cls.term = AcademicTerm.objects.create(
            school=cls.school, academic_year=cls.year, name='Term 1',
            term_type='term_1', start_date=date(2026, 1, 1),
            end_date=date(2026, 6, 30), is_active=True,
        )
        cls.other_term = AcademicTerm.objects.create(
            school=cls.other_school, academic_year=cls.other_year, name='Term 1',
            term_type='term_1', start_date=date(2026, 1, 1),
            end_date=date(2026, 6, 30), is_active=True,
        )
        cls.classroom = Classroom.objects.create(
            school=cls.school, academic_year=cls.year, name='Grade 8', code='G8',
        )
        cls.other_classroom = Classroom.objects.create(
            school=cls.other_school, academic_year=cls.other_year,
            name='Grade 8', code='G8',
        )
        cls.section = Section.objects.create(
            school=cls.school, academic_year=cls.year, classroom=cls.classroom,
            name='A', code='A',
        )
        cls.other_section = Section.objects.create(
            school=cls.other_school, academic_year=cls.other_year,
            classroom=cls.other_classroom, name='A', code='A',
        )
        cls.subject = Subject.objects.create(school=cls.school, name='Math', code='MATH')
        cls.other_subject = Subject.objects.create(
            school=cls.other_school, name='Math', code='MATH',
        )
        cls.admin_user = User.objects.create_user(
            username='s3-admin', password=cls.password, role='school_admin',
            school=cls.school, academic_year=cls.year, is_staff=True,
        )
        cls.teacher_user = User.objects.create_user(
            username='s3-teacher', password=cls.password, role='teacher',
            school=cls.school, academic_year=cls.year,
        )
        cls.other_teacher_user = User.objects.create_user(
            username='s3-other-teacher', password=cls.password, role='teacher',
            school=cls.other_school, academic_year=cls.other_year,
        )
        cls.parent_user = User.objects.create_user(
            username='s3-parent', password=cls.password, role='parent', school=cls.school,
        )
        cls.student_user = User.objects.create_user(
            username='s3-student', password=cls.password, role='student', school=cls.school,
        )
        cls.super_user = User.objects.create_user(
            username='s3-super', password=cls.password, role='super_admin',
            is_staff=True, is_superuser=True,
        )
        cls.teacher = Teacher.objects.create(
            school=cls.school, academic_year=cls.year, user=cls.teacher_user,
            full_name='Teacher One', employee_code='S3A-T90001',
        )
        cls.other_teacher = Teacher.objects.create(
            school=cls.other_school, academic_year=cls.other_year,
            user=cls.other_teacher_user, full_name='Teacher Other',
            employee_code='S3B-T90001',
        )
        cls.assignment = TeacherAssignment.objects.create(
            teacher=cls.teacher, school=cls.school, academic_year=cls.year,
            classroom=cls.classroom, section=cls.section, subject=cls.subject,
        )
        cls.other_assignment = TeacherAssignment.objects.create(
            teacher=cls.other_teacher, school=cls.other_school,
            academic_year=cls.other_year, classroom=cls.other_classroom,
            section=cls.other_section, subject=cls.other_subject,
        )
        cls.student = Student.objects.create(
            school=cls.school, user=cls.student_user, full_name='Student One',
            student_code='S3A-S90001', gender='male',
        )
        cls.student_two = Student.objects.create(
            school=cls.school, full_name='Student Two',
            student_code='S3A-S90002', gender='female',
        )
        cls.other_student = Student.objects.create(
            school=cls.other_school, full_name='Other Student',
            student_code='S3B-S90001', gender='male',
        )
        cls.enrollment = StudentEnrollment.objects.create(
            student=cls.student, school=cls.school, academic_year=cls.year,
            classroom=cls.classroom, section=cls.section,
        )
        cls.enrollment_two = StudentEnrollment.objects.create(
            student=cls.student_two, school=cls.school, academic_year=cls.year,
            classroom=cls.classroom, section=cls.section,
        )
        cls.other_enrollment = StudentEnrollment.objects.create(
            student=cls.other_student, school=cls.other_school,
            academic_year=cls.other_year, classroom=cls.other_classroom,
            section=cls.other_section,
        )
        cls.parent = Parent.objects.create(
            school=cls.school, user=cls.parent_user, full_name='Parent One',
            parent_code='S3A-P90001',
        )
        StudentGuardian.objects.create(
            student=cls.student, parent=cls.parent, relationship='father',
        )
        cls.exam_type = ExamType.objects.create(
            school=cls.school, name='Midterm', code='MID', max_score=100,
            weight_percentage=40,
        )
        cls.other_exam_type = ExamType.objects.create(
            school=cls.other_school, name='Midterm', code='MID', max_score=100,
        )
        cls.exam = Exam.objects.create(
            school=cls.school, academic_year=cls.year, academic_term=cls.term,
            teacher_assignment=cls.assignment, exam_type=cls.exam_type,
            created_by=cls.teacher_user, title='Math Midterm',
            exam_date=date(2026, 3, 10), total_marks=100,
        )
        cls.other_exam = Exam.objects.create(
            school=cls.other_school, academic_year=cls.other_year,
            academic_term=cls.other_term, teacher_assignment=cls.other_assignment,
            exam_type=cls.other_exam_type, created_by=cls.other_teacher_user,
            title='Other Math Midterm', exam_date=date(2026, 3, 10), total_marks=100,
        )
        cls.result = ExamResult.objects.create(
            exam=cls.exam, student_enrollment=cls.enrollment,
            score=Decimal('80'), status='present', graded_by=cls.teacher_user,
        )
        cls.other_result = ExamResult.objects.create(
            exam=cls.other_exam, student_enrollment=cls.other_enrollment,
            score=Decimal('75'), status='present', graded_by=cls.other_teacher_user,
        )

    def auth(self, user=None):
        user = user or self.teacher_user
        membership = ensure_legacy_membership(user)
        credentials = {
            'HTTP_AUTHORIZATION': f'Bearer {RefreshToken.for_user(user).access_token}',
        }
        if membership is not None:
            credentials['HTTP_X_SCHOOL_MEMBERSHIP_ID'] = str(membership.pk)
        self.client.force_authenticate(user=None)
        self.client.credentials(**credentials)

    def submit_result(self):
        self.auth(self.teacher_user)
        return self.client.post(f'/api/v1/exam-results/{self.result.pk}/submit/', {})

    def approve_result(self):
        self.submit_result()
        self.auth(self.admin_user)
        return self.client.post(f'/api/v1/exam-results/{self.result.pk}/approve/', {})

    def test_01_unauthenticated_exam_list_is_401(self):
        self.assertEqual(self.client.get('/api/v1/exams/').status_code, 401)

    def test_02_teacher_can_list_exam_types(self):
        self.auth()
        response = self.client.get('/api/v1/exam-types/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 1)

    def test_03_teacher_cannot_create_exam_type(self):
        self.auth()
        response = self.client.post('/api/v1/exam-types/', {
            'name': 'Quiz', 'code': 'Q', 'max_score': 20, 'weight_percentage': 10,
        })
        self.assertEqual(response.status_code, 403)

    def test_04_school_admin_creates_exam_type_in_own_school(self):
        self.auth(self.admin_user)
        response = self.client.post('/api/v1/exam-types/', {
            'name': 'Quiz', 'code': 'Q', 'max_score': 20, 'weight_percentage': 10,
        })
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['school'], self.school.pk)

    def test_05_exam_type_outside_tenant_is_404(self):
        self.auth(self.admin_user)
        response = self.client.get(f'/api/v1/exam-types/{self.other_exam_type.pk}/')
        self.assertEqual(response.status_code, 404)

    def test_06_teacher_creates_draft_exam(self):
        self.auth()
        response = self.client.post('/api/v1/exams/', {
            'academic_year': self.year.pk, 'academic_term': self.term.pk,
            'teacher_assignment': self.assignment.pk, 'exam_type': self.exam_type.pk,
            'title': 'Final', 'exam_date': '2026-05-01', 'total_marks': '100',
            'status': 'published',
        })
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['status'], 'draft')

    def test_07_teacher_cannot_create_exam_for_other_tenant(self):
        self.auth()
        response = self.client.post('/api/v1/exams/', {
            'academic_year': self.other_year.pk, 'academic_term': self.other_term.pk,
            'teacher_assignment': self.other_assignment.pk,
            'exam_type': self.other_exam_type.pk, 'title': 'Escape',
            'exam_date': '2026-03-01', 'total_marks': '100',
        })
        self.assertEqual(response.status_code, 400)

    def test_08_teacher_updates_own_draft_exam(self):
        self.auth()
        response = self.client.patch(
            f'/api/v1/exams/{self.exam.pk}/', {'notes': 'Updated'}, format='json',
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['notes'], 'Updated')

    def test_09_teacher_deletes_empty_draft_exam(self):
        empty = Exam.objects.create(
            school=self.school, academic_year=self.year, academic_term=self.term,
            teacher_assignment=self.assignment, exam_type=self.exam_type,
            created_by=self.teacher_user, title='Empty', exam_date=date(2026, 4, 1),
            total_marks=100,
        )
        self.auth()
        self.assertEqual(self.client.delete(f'/api/v1/exams/{empty.pk}/').status_code, 204)

    def test_10_exam_with_results_cannot_be_deleted(self):
        self.auth()
        self.assertEqual(self.client.delete(f'/api/v1/exams/{self.exam.pk}/').status_code, 400)

    def test_11_teacher_creates_result_and_audit_log(self):
        self.auth()
        response = self.client.post('/api/v1/exam-results/', {
            'exam': self.exam.pk, 'student_enrollment': self.enrollment_two.pk,
            'score': '70', 'status': 'present', 'remarks': 'Good',
        })
        self.assertEqual(response.status_code, 201)
        self.assertTrue(ExamResultLog.objects.filter(
            exam_result_id=response.data['id'], action='create',
        ).exists())

    def test_12_teacher_updates_draft_result_via_service(self):
        self.auth()
        response = self.client.patch(
            f'/api/v1/exam-results/{self.result.pk}/', {'score': '85'}, format='json',
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(ExamResultLog.objects.filter(
            exam_result=self.result, action='update', new_score=85,
        ).exists())

    def test_13_negative_score_is_rejected(self):
        self.auth()
        response = self.client.patch(
            f'/api/v1/exam-results/{self.result.pk}/', {'score': '-1'}, format='json',
        )
        self.assertEqual(response.status_code, 400)

    def test_14_score_above_total_is_rejected(self):
        self.auth()
        response = self.client.patch(
            f'/api/v1/exam-results/{self.result.pk}/', {'score': '101'}, format='json',
        )
        self.assertEqual(response.status_code, 400)

    def test_15_cross_tenant_enrollment_is_rejected(self):
        self.auth()
        response = self.client.post('/api/v1/exam-results/', {
            'exam': self.exam.pk, 'student_enrollment': self.other_enrollment.pk,
            'score': '70', 'status': 'present',
        })
        self.assertEqual(response.status_code, 400)

    def test_16_duplicate_exam_result_is_rejected(self):
        self.auth()
        response = self.client.post('/api/v1/exam-results/', {
            'exam': self.exam.pk, 'student_enrollment': self.enrollment.pk,
            'score': '70', 'status': 'present',
        })
        self.assertEqual(response.status_code, 400)

    def test_17_bulk_creates_results_atomically(self):
        self.auth()
        response = self.client.post('/api/v1/exam-results/bulk/', {
            'exam': self.exam.pk,
            'results': [{'student_enrollment': self.enrollment_two.pk, 'score': '65', 'status': 'present'}],
        }, format='json')
        self.assertEqual(response.status_code, 200)
        created = ExamResult.objects.get(
            exam=self.exam, student_enrollment=self.enrollment_two, score=65,
        )
        self.assertTrue(ExamResultLog.objects.filter(
            exam_result=created, action='create',
        ).exists())

    def test_18_bulk_updates_existing_result(self):
        self.auth()
        response = self.client.post('/api/v1/exam-results/bulk/', {
            'exam': self.exam.pk,
            'results': [{'student_enrollment': self.enrollment.pk, 'score': '91', 'status': 'present'}],
        }, format='json')
        self.assertEqual(response.status_code, 200)
        self.result.refresh_from_db()
        self.assertEqual(self.result.score, Decimal('91'))
        self.assertTrue(ExamResultLog.objects.filter(
            exam_result=self.result, action='update', new_score=91,
        ).exists())

    def test_19_bulk_rejects_duplicate_students(self):
        self.auth()
        item = {'student_enrollment': self.enrollment_two.pk, 'score': '60', 'status': 'present'}
        response = self.client.post('/api/v1/exam-results/bulk/', {
            'exam': self.exam.pk, 'results': [item, item],
        }, format='json')
        self.assertEqual(response.status_code, 400)

    def test_20_bulk_validation_prevents_partial_write(self):
        self.auth()
        before = ExamResult.objects.count()
        response = self.client.post('/api/v1/exam-results/bulk/', {
            'exam': self.exam.pk,
            'results': [
                {'student_enrollment': self.enrollment_two.pk, 'score': '60', 'status': 'present'},
                {'student_enrollment': self.other_enrollment.pk, 'score': '60', 'status': 'present'},
            ],
        }, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(ExamResult.objects.count(), before)

    def test_21_teacher_submits_graded_result(self):
        response = self.submit_result()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['workflow_status'], 'submitted')
        self.assertTrue(ExamResultLog.objects.filter(
            exam_result=self.result, action='submit',
        ).exists())

    def test_22_ungraded_result_cannot_be_submitted(self):
        result = ExamResult.objects.create(
            exam=self.exam, student_enrollment=self.enrollment_two, status='not_graded',
        )
        self.auth()
        response = self.client.post(f'/api/v1/exam-results/{result.pk}/submit/', {})
        self.assertEqual(response.status_code, 400)

    def test_23_teacher_cannot_approve(self):
        self.submit_result()
        self.auth(self.teacher_user)
        response = self.client.post(f'/api/v1/exam-results/{self.result.pk}/approve/', {})
        self.assertEqual(response.status_code, 403)

    def test_24_school_admin_approves_submitted_result(self):
        response = self.approve_result()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['workflow_status'], 'approved')
        self.assertEqual(response.data['approved_by'], self.admin_user.pk)
        self.assertTrue(ExamResultLog.objects.filter(
            exam_result=self.result, action='approve',
        ).exists())

    def test_25_approved_result_is_read_only_for_teacher(self):
        self.approve_result()
        self.auth()
        response = self.client.patch(
            f'/api/v1/exam-results/{self.result.pk}/', {'score': '90'}, format='json',
        )
        self.assertEqual(response.status_code, 400)

    def test_26_school_admin_reopens_approved_result(self):
        self.approve_result()
        self.auth(self.admin_user)
        response = self.client.post(
            f'/api/v1/exam-results/{self.result.pk}/reopen/', {'reason': 'Correction'},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['workflow_status'], 'draft')
        self.assertTrue(ExamResultLog.objects.filter(
            exam_result=self.result, action='reopen',
        ).exists())

    def test_27_reject_requires_reason(self):
        self.submit_result()
        self.auth(self.admin_user)
        response = self.client.post(f'/api/v1/exam-results/{self.result.pk}/reject/', {})
        self.assertEqual(response.status_code, 400)

    def test_28_reject_returns_to_draft_and_keeps_reason(self):
        self.submit_result()
        self.auth(self.admin_user)
        response = self.client.post(
            f'/api/v1/exam-results/{self.result.pk}/reject/', {'reason': 'Recheck marks'},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['workflow_status'], 'draft')
        self.assertEqual(response.data['approval_reason'], 'Recheck marks')
        self.assertTrue(ExamResultLog.objects.filter(
            exam_result=self.result, action='reject', reason='Recheck marks',
        ).exists())

    def test_29_parent_sees_only_approved_results(self):
        self.auth(self.parent_user)
        self.assertEqual(self.client.get('/api/v1/parents/me/results/').data['count'], 0)
        self.result.workflow_status = 'approved'
        self.result.approved_by = self.admin_user
        self.result.approved_at = timezone.now()
        self.result.is_published = True
        self.result.published_by = self.admin_user
        self.result.published_at = timezone.now()
        self.result.save()
        response = self.client.get('/api/v1/parents/me/results/')
        self.assertEqual(response.data['count'], 1)

    def test_30_student_sees_only_approved_results(self):
        self.auth(self.student_user)
        self.assertEqual(self.client.get('/api/v1/students/me/results/').data['count'], 0)
        self.result.workflow_status = 'approved'
        self.result.approved_by = self.admin_user
        self.result.approved_at = timezone.now()
        self.result.is_published = True
        self.result.published_by = self.admin_user
        self.result.published_at = timezone.now()
        self.result.save()
        response = self.client.get('/api/v1/students/me/results/')
        self.assertEqual(response.data['count'], 1)
        payload = response.data['results'][0]
        self.assertEqual(payload['exam_type_id'], self.exam_type.id)
        self.assertEqual(payload['exam_type_name'], 'Midterm')
        self.assertEqual(payload['exam_type_code'], 'MID')
        self.assertEqual(str(payload['total_marks']), '100.00')
        self.assertEqual(float(payload['percentage']), 80.0)

    def test_31_teacher_sees_only_own_assignment_results(self):
        self.auth()
        response = self.client.get('/api/v1/teachers/me/results/')
        self.assertEqual(response.data['count'], 1)

    def test_32_cross_tenant_result_returns_404(self):
        self.auth(self.admin_user)
        response = self.client.get(f'/api/v1/exam-results/{self.other_result.pk}/')
        self.assertEqual(response.status_code, 404)

    def test_33_audit_captures_request_metadata(self):
        self.auth()
        self.client.patch(
            f'/api/v1/exam-results/{self.result.pk}/', {'score': '82'}, format='json',
            HTTP_X_REQUEST_ID='req-sprint3', HTTP_USER_AGENT='Sprint3Agent',
            REMOTE_ADDR='127.0.0.9',
        )
        log = ExamResultLog.objects.filter(exam_result=self.result).latest('changed_at')
        self.assertEqual(log.request_id, 'req-sprint3')
        self.assertEqual(log.ip_address, '127.0.0.9')
        self.assertEqual(log.user_agent, 'Sprint3Agent')

    def test_34_parent_cannot_view_audit_logs(self):
        self.auth(self.parent_user)
        response = self.client.get(f'/api/v1/exam-results/{self.result.pk}/logs/')
        self.assertEqual(response.status_code, 403)

    def test_35_student_transcript_contains_statistics(self):
        self.result.workflow_status = 'approved'
        self.result.approved_by = self.admin_user
        self.result.approved_at = timezone.now()
        self.result.is_published = True
        self.result.published_by = self.admin_user
        self.result.published_at = timezone.now()
        self.result.save()
        self.auth(self.student_user)
        response = self.client.get(
            f'/api/v1/exam-results/reports/student/{self.student.pk}/transcript/',
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['statistics']['pass_count'], 1)

    def test_36_class_summary_statistics(self):
        self.result.workflow_status = 'approved'
        self.result.approved_by = self.admin_user
        self.result.approved_at = timezone.now()
        self.result.is_published = True
        self.result.published_by = self.admin_user
        self.result.published_at = timezone.now()
        self.result.save()
        self.auth()
        response = self.client.get(
            f'/api/v1/exam-results/reports/class/{self.classroom.pk}/summary/',
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['statistics']['highest'], Decimal('80'))

    def test_37_subject_summary_statistics(self):
        self.result.workflow_status = 'approved'
        self.result.approved_by = self.admin_user
        self.result.approved_at = timezone.now()
        self.result.is_published = True
        self.result.published_by = self.admin_user
        self.result.published_at = timezone.now()
        self.result.save()
        self.auth()
        response = self.client.get(
            f'/api/v1/exam-results/reports/subject/{self.subject.pk}/summary/',
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['statistics']['pass_rate'], 100.0)

    def test_38_exam_summary_statistics(self):
        self.result.workflow_status = 'approved'
        self.result.approved_by = self.admin_user
        self.result.approved_at = timezone.now()
        self.result.is_published = True
        self.result.published_by = self.admin_user
        self.result.published_at = timezone.now()
        self.result.save()
        self.auth()
        response = self.client.get(
            f'/api/v1/exam-results/reports/exam/{self.exam.pk}/summary/',
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['statistics']['average'], Decimal('80'))

    def test_39_result_list_avoids_n_plus_one(self):
        self.auth()
        with CaptureQueriesContext(connection) as queries:
            response = self.client.get('/api/v1/exam-results/')
        self.assertEqual(response.status_code, 200)
        self.assertLessEqual(len(queries), 8)

    def test_40_openapi_contains_workflow_and_bulk_paths(self):
        self.auth(self.admin_user)
        content = self.client.get('/api/schema/').content.decode('utf-8')
        self.assertIn('/api/v1/exam-results/bulk/', content)
        self.assertIn('/api/v1/exam-results/{id}/approve/', content)

    def test_41_exam_result_log_admin_is_fully_read_only(self):
        model_admin = ExamResultLogAdmin(ExamResultLog, admin.site)
        request = RequestFactory().get('/admin/')
        request.user = self.super_user
        self.assertFalse(model_admin.has_add_permission(request))
        self.assertFalse(model_admin.has_change_permission(request))
        self.assertFalse(model_admin.has_delete_permission(request))

    def test_42_exam_result_admin_workflow_fields_are_read_only(self):
        model_admin = ExamResultAdmin(ExamResult, admin.site)
        self.assertIn('workflow_status', model_admin.readonly_fields)
        self.assertIn('approved_by', model_admin.readonly_fields)
        request = RequestFactory().get('/admin/')
        request.user = self.super_user
        self.assertFalse(model_admin.has_delete_permission(request, self.result))

    def test_43_logs_are_visible_to_teacher_for_own_result(self):
        self.auth()
        self.client.patch(
            f'/api/v1/exam-results/{self.result.pk}/', {'score': '81'}, format='json',
        )
        response = self.client.get(f'/api/v1/exam-results/{self.result.pk}/logs/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
    def test_44_teacher_deletes_draft_result(self):
        result = ExamResult.objects.create(
            exam=self.exam, student_enrollment=self.enrollment_two,
            score=Decimal('60'), status='present', graded_by=self.teacher_user,
        )
        self.auth()
        response = self.client.delete(f'/api/v1/exam-results/{result.pk}/')
        self.assertEqual(response.status_code, 204)
        self.assertFalse(ExamResult.objects.filter(pk=result.pk).exists())

    def test_45_manager_reports_include_non_approved_results(self):
        self.auth()
        response = self.client.get(
            f'/api/v1/exam-results/reports/exam/{self.exam.pk}/summary/',
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['statistics']['total_results'], 1)

    def test_46_inactive_school_user_is_forbidden(self):
        self.teacher_user.is_active_school_user = False
        self.teacher_user.save(update_fields=['is_active_school_user'])
        self.auth()
        self.assertEqual(self.client.get('/api/v1/exams/').status_code, 403)
