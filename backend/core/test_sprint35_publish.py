from datetime import date
from unittest.mock import patch

from django.contrib import admin
from django.core.exceptions import ValidationError
from django.test import RequestFactory
from django.contrib.messages.storage.fallback import FallbackStorage
from django.utils import timezone
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from .admin import ExamAdmin
from .models import Exam, ExamResult, ExamResultLog
from .context import ensure_legacy_membership
from . import test_sprint3_exams


class SprintThreePointFivePublishTests(APITestCase):
    password = test_sprint3_exams.SprintThreeExamPlatformTests.password
    setUpTestData = classmethod(
        test_sprint3_exams.SprintThreeExamPlatformTests.setUpTestData.__func__
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

    def approve(self, result=None):
        result = result or self.result
        result.workflow_status = 'approved'
        result.approved_by = self.admin_user
        result.approved_at = timezone.now()
        result.save()
        return result

    def publish(self, exam=None, user=None, reason='Ready'):
        self.auth(user or self.admin_user)
        exam = exam or self.exam
        return self.client.post(
            f'/api/v1/exams/{exam.pk}/publish/', {'reason': reason}, format='json',
        )

    def make_exam(self, title='Second Exam'):
        exam = Exam.objects.create(
            school=self.school, academic_year=self.year, academic_term=self.term,
            teacher_assignment=self.assignment, exam_type=self.exam_type,
            created_by=self.teacher_user, title=title,
            exam_date=date(2026, 4, 10), total_marks=100,
        )
        result = ExamResult.objects.create(
            exam=exam, student_enrollment=self.enrollment,
            score=70, status='present', graded_by=self.teacher_user,
        )
        return exam, result

    def test_47_publish_requires_all_results_approved(self):
        response = self.publish()
        self.assertEqual(response.status_code, 400)
        self.result.refresh_from_db()
        self.assertFalse(self.result.is_published)

    def test_48_publish_sets_metadata_and_returns_standard_results(self):
        self.approve()
        response = self.publish()
        self.assertEqual(response.status_code, 200)
        self.result.refresh_from_db()
        self.assertTrue(self.result.is_published)
        self.assertEqual(self.result.published_by, self.admin_user)
        self.assertIsNotNone(self.result.published_at)
        self.assertEqual(response.data['published_count'], 1)
        self.assertTrue(response.data['results'][0]['is_published'])

    def test_49_publish_creates_complete_audit_log(self):
        self.approve()
        self.publish(reason='Term release')
        log = ExamResultLog.objects.get(exam_result=self.result, action='publish')
        self.assertFalse(log.old_is_published)
        self.assertTrue(log.new_is_published)
        self.assertEqual(log.published_by, self.admin_user)
        self.assertEqual(log.reason, 'Term release')

    def test_50_unpublish_clears_metadata_and_audits(self):
        self.approve(); self.publish()
        response = self.client.post(
            f'/api/v1/exams/{self.exam.pk}/unpublish/', {'reason': 'Correction'},
            format='json',
        )
        self.assertEqual(response.status_code, 200)
        self.result.refresh_from_db()
        self.assertFalse(self.result.is_published)
        self.assertIsNone(self.result.published_by)
        self.assertIsNone(self.result.published_at)
        self.assertTrue(ExamResultLog.objects.filter(
            exam_result=self.result, action='unpublish',
            old_is_published=True, new_is_published=False,
        ).exists())

    def test_51_teacher_cannot_publish(self):
        self.approve()
        self.assertEqual(self.publish(user=self.teacher_user).status_code, 403)

    def test_52_student_and_parent_cannot_see_approved_unpublished_result(self):
        self.approve()
        for user, url in ((self.student_user, '/api/v1/students/me/results/'),
                          (self.parent_user, '/api/v1/parents/me/results/')):
            self.auth(user)
            self.assertEqual(self.client.get(url).data['count'], 0)

    def test_53_student_and_parent_see_published_result(self):
        self.approve(); self.publish()
        for user, url in ((self.student_user, '/api/v1/students/me/results/'),
                          (self.parent_user, '/api/v1/parents/me/results/')):
            self.auth(user)
            self.assertEqual(self.client.get(url).data['count'], 1)

    def test_54_cross_tenant_publish_is_404(self):
        self.auth(self.admin_user)
        response = self.client.post(f'/api/v1/exams/{self.other_exam.pk}/publish/', {})
        self.assertEqual(response.status_code, 404)

    def test_55_publish_skips_non_approved_results_with_summary(self):
        self.approve()
        skipped = ExamResult.objects.create(
            exam=self.exam, student_enrollment=self.enrollment_two,
            score=60, status='present', graded_by=self.teacher_user,
        )
        response = self.publish()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['published_count'], 1)
        self.assertEqual(response.data['skipped_count'], 1)
        skipped.refresh_from_db()
        self.assertFalse(skipped.is_published)

    def test_56_bulk_publish_publishes_multiple_exams(self):
        self.approve()
        exam_two, result_two = self.make_exam(); self.approve(result_two)
        self.auth(self.admin_user)
        response = self.client.post('/api/v1/exams/bulk-publish/', {
            'exam_ids': [self.exam.pk, exam_two.pk], 'reason': 'Bulk release',
        }, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(ExamResult.objects.filter(is_published=True).count(), 2)

    def test_57_bulk_publish_rejects_duplicates(self):
        self.auth(self.admin_user)
        response = self.client.post('/api/v1/exams/bulk-publish/', {
            'exam_ids': [self.exam.pk, self.exam.pk],
        }, format='json')
        self.assertEqual(response.status_code, 400)

    def test_58_bulk_publish_rolls_back_all_exams(self):
        self.approve()
        exam_two, _ = self.make_exam()
        self.auth(self.admin_user)
        response = self.client.post('/api/v1/exams/bulk-publish/', {
            'exam_ids': [self.exam.pk, exam_two.pk],
        }, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertFalse(ExamResult.objects.filter(is_published=True).exists())

    def test_59_reopen_unpublishes_before_returning_to_draft(self):
        self.approve(); self.publish()
        response = self.client.post(
            f'/api/v1/exam-results/{self.result.pk}/reopen/', {'reason': 'Edit'},
            HTTP_X_REQUEST_ID='reopen-request', HTTP_USER_AGENT='Sprint35',
            REMOTE_ADDR='127.0.0.35',
        )
        self.assertEqual(response.status_code, 200)
        self.result.refresh_from_db()
        self.assertEqual(self.result.workflow_status, 'draft')
        self.assertFalse(self.result.is_published)
        self.assertIsNone(self.result.published_by)
        self.assertIsNone(self.result.published_at)
        actions = list(ExamResultLog.objects.filter(
            exam_result=self.result,
        ).order_by('-changed_at').values_list('action', flat=True)[:2])
        self.assertEqual(actions, ['reopen', 'unpublish'])
        unpublish_log = ExamResultLog.objects.filter(
            exam_result=self.result, action='unpublish',
        ).latest('changed_at')
        self.assertEqual(unpublish_log.request_id, 'reopen-request')
        self.assertEqual(unpublish_log.ip_address, '127.0.0.35')
        self.assertEqual(unpublish_log.user_agent, 'Sprint35')

    def test_60_notification_extension_point_is_invoked_after_commit(self):
        self.approve()
        with patch('core.services.exam_results.notify_results_published') as notify:
            with self.captureOnCommitCallbacks(execute=True):
                self.publish()
        notify.assert_called_once_with(
            exam_id=self.exam.pk, result_ids=(self.result.pk,),
        )

    def test_61_admin_exposes_actions_and_published_count(self):
        self.approve(); self.publish()
        model_admin = ExamAdmin(Exam, admin.site)
        request = RequestFactory().get('/admin/')
        request.user = self.admin_user
        exam = model_admin.get_queryset(request).get(pk=self.exam.pk)
        self.assertEqual(model_admin.published_results_count(exam), 1)
        self.assertIn('publish_selected_results', model_admin.actions)

    def test_62_openapi_contains_publish_paths(self):
        self.auth(self.admin_user)
        content = self.client.get('/api/schema/').content.decode('utf-8')
        self.assertIn('/api/v1/exams/{id}/publish/', content)
        self.assertIn('/api/v1/exams/bulk-publish/', content)


    def test_63_unauthenticated_publish_is_401(self):
        self.client.force_authenticate(user=None)
        self.client.credentials()
        response = self.client.post(f'/api/v1/exams/{self.exam.pk}/publish/', {})
        self.assertEqual(response.status_code, 401)

    def test_64_parent_and_student_cannot_publish(self):
        self.approve()
        for user in (self.parent_user, self.student_user):
            self.assertEqual(self.publish(user=user).status_code, 403)

    def test_65_submitted_and_rejected_results_are_not_publishable(self):
        for workflow_status in ('submitted', 'rejected'):
            self.result.workflow_status = workflow_status
            self.result.approved_by = None
            self.result.approved_at = None
            self.result.save()
            response = self.publish()
            self.assertEqual(response.status_code, 400)
            self.result.refresh_from_db()
            self.assertFalse(self.result.is_published)

    def test_66_teacher_visibility_is_independent_of_publication(self):
        self.auth(self.teacher_user)
        response = self.client.get('/api/v1/teachers/me/results/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 1)

    def test_67_publish_audit_captures_request_metadata(self):
        self.approve()
        self.auth(self.admin_user)
        self.client.post(
            f'/api/v1/exams/{self.exam.pk}/publish/', {'reason': 'Release'},
            format='json', HTTP_X_REQUEST_ID='publish-request',
            HTTP_USER_AGENT='Sprint35', REMOTE_ADDR='127.0.0.36',
        )
        log = ExamResultLog.objects.get(exam_result=self.result, action='publish')
        self.assertEqual(log.request_id, 'publish-request')
        self.assertEqual(log.ip_address, '127.0.0.36')
        self.assertEqual(log.user_agent, 'Sprint35')

    def test_68_teacher_staff_does_not_receive_publish_admin_actions(self):
        self.teacher_user.is_staff = True
        self.teacher_user.save(update_fields=['is_staff'])
        model_admin = ExamAdmin(Exam, admin.site)
        request = RequestFactory().get('/admin/')
        request.user = self.teacher_user
        actions = model_admin.get_actions(request)
        self.assertNotIn('publish_selected_results', actions)
        self.assertNotIn('unpublish_selected_results', actions)

    def test_69_new_results_default_to_unpublished(self):
        _, result = self.make_exam(title='Default publication state')
        self.assertFalse(result.is_published)
        self.assertIsNone(result.published_at)
        self.assertIsNone(result.published_by)


    def test_70_admin_publish_action_is_scoped_and_audited(self):
        self.approve()
        model_admin = ExamAdmin(Exam, admin.site)
        request = RequestFactory().post('/admin/core/exam/')
        request.user = self.admin_user
        request.session = {}
        request._messages = FallbackStorage(request)
        queryset = model_admin.get_queryset(request)
        self.assertFalse(queryset.filter(pk=self.other_exam.pk).exists())
        model_admin.publish_selected_results(
            request, queryset.filter(pk=self.exam.pk),
        )
        self.result.refresh_from_db()
        self.assertTrue(self.result.is_published)
        self.assertTrue(ExamResultLog.objects.filter(
            exam_result=self.result, action='publish', changed_by=self.admin_user,
        ).exists())

    def test_71_student_and_parent_transcript_hide_unpublished_results(self):
        self.approve()
        for user in (self.student_user, self.parent_user):
            self.auth(user)
            response = self.client.get(
                f'/api/v1/exam-results/reports/student/{self.student.pk}/transcript/',
            )
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.data['statistics']['total_results'], 0)
        self.publish()
        for user in (self.student_user, self.parent_user):
            self.auth(user)
            response = self.client.get(
                f'/api/v1/exam-results/reports/student/{self.student.pk}/transcript/',
            )
            self.assertEqual(response.data['statistics']['total_results'], 1)


    def test_72_notification_failure_does_not_rollback_publication(self):
        self.approve()
        with patch(
            'core.services.exam_results.notify_results_published',
            side_effect=RuntimeError('provider unavailable'),
        ):
            with self.captureOnCommitCallbacks(execute=True):
                response = self.publish()
        self.assertEqual(response.status_code, 200)
        self.result.refresh_from_db()
        self.assertTrue(self.result.is_published)

    def test_73_school_admin_publisher_must_match_exam_school(self):
        self.result.workflow_status = 'approved'
        self.result.approved_by = self.admin_user
        self.result.approved_at = timezone.now()
        self.result.is_published = True
        self.result.published_by = self.other_teacher_user
        self.result.published_by.role = 'school_admin'
        self.result.published_by.save(update_fields=['role'])
        self.result.published_at = timezone.now()
        with self.assertRaises(ValidationError):
            self.result.save()
