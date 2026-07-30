from datetime import date
from unittest.mock import patch

from django.contrib import admin, messages
from django.contrib.messages import get_messages
from django.contrib.messages.storage.fallback import FallbackStorage
from django.db import IntegrityError, transaction
from django.test import RequestFactory, override_settings
from django.utils import timezone
from rest_framework.test import APITestCase

from . import test_sprint3_exams
from .admin import ExamAdmin
from .models import Exam, ExamResult
from .services.exam_results import request_audit_metadata


class SprintThreePointFiveHardeningTests(APITestCase):
    password = test_sprint3_exams.SprintThreeExamPlatformTests.password
    setUpTestData = classmethod(
        test_sprint3_exams.SprintThreeExamPlatformTests.setUpTestData.__func__
    )

    def auth(self, user=None):
        self.client.force_authenticate(user=user or self.admin_user)

    def approve(self, result=None):
        result = result or self.result
        result.workflow_status = 'approved'
        result.approved_by = self.admin_user
        result.approved_at = timezone.now()
        result.save()
        return result

    def make_exam(self, title='Hardening exam'):
        exam = Exam.objects.create(
            school=self.school, academic_year=self.year, academic_term=self.term,
            teacher_assignment=self.assignment, exam_type=self.exam_type,
            created_by=self.teacher_user, title=title,
            exam_date=date(2026, 5, 10), total_marks=100,
        )
        result = ExamResult.objects.create(
            exam=exam, student_enrollment=self.enrollment,
            score=75, status='present', graded_by=self.teacher_user,
        )
        return exam, result

    def admin_request(self):
        request = RequestFactory().post('/admin/core/exam/')
        request.user = self.admin_user
        request.session = {}
        request._messages = FallbackStorage(request)
        return request

    def test_notification_is_not_called_before_commit(self):
        self.approve()
        self.auth()
        with patch('core.services.exam_results.notify_results_published') as notify:
            with self.captureOnCommitCallbacks(execute=False) as callbacks:
                response = self.client.post(
                    f'/api/v1/exams/{self.exam.pk}/publish/', {}, format='json',
                )
                self.assertEqual(response.status_code, 200)
                notify.assert_not_called()
            self.assertEqual(len(callbacks), 1)
            notify.assert_not_called()

    def test_notification_is_called_after_successful_commit(self):
        self.approve()
        self.auth()
        with patch('core.services.exam_results.notify_results_published') as notify:
            with self.captureOnCommitCallbacks(execute=True):
                self.client.post(
                    f'/api/v1/exams/{self.exam.pk}/publish/', {}, format='json',
                )
        notify.assert_called_once_with(
            exam_id=self.exam.pk, result_ids=(self.result.pk,),
        )

    def test_bulk_rollback_registers_no_notification(self):
        self.approve()
        exam_two, _ = self.make_exam('Invalid bulk exam')
        self.auth()
        with patch('core.services.exam_results.notify_results_published') as notify:
            with self.captureOnCommitCallbacks(execute=True) as callbacks:
                response = self.client.post('/api/v1/exams/bulk-publish/', {
                    'exam_ids': [self.exam.pk, exam_two.pk],
                }, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(callbacks, [])
        notify.assert_not_called()
        self.result.refresh_from_db()
        self.assertFalse(self.result.is_published)

    def test_notification_failure_after_commit_does_not_rollback(self):
        self.approve()
        self.auth()
        with patch(
            'core.services.exam_results.notify_results_published',
            side_effect=RuntimeError('provider unavailable'),
        ):
            with self.captureOnCommitCallbacks(execute=True):
                response = self.client.post(
                    f'/api/v1/exams/{self.exam.pk}/publish/', {}, format='json',
                )
        self.assertEqual(response.status_code, 200)
        self.result.refresh_from_db()
        self.assertTrue(self.result.is_published)

    def test_admin_publish_and_unpublish_actions_report_counts(self):
        self.approve()
        model_admin = ExamAdmin(Exam, admin.site)
        request = self.admin_request()
        queryset = model_admin.get_queryset(request).filter(pk=self.exam.pk)
        model_admin.publish_selected_results(request, queryset)
        first_messages = list(get_messages(request))
        self.assertEqual(first_messages[-1].level, messages.SUCCESS)
        self.assertIn('Published 1 result(s).', str(first_messages[-1]))
        self.result.refresh_from_db()
        self.assertTrue(self.result.is_published)

        request = self.admin_request()
        queryset = model_admin.get_queryset(request).filter(pk=self.exam.pk)
        model_admin.unpublish_selected_results(request, queryset)
        second_messages = list(get_messages(request))
        self.assertEqual(second_messages[-1].level, messages.SUCCESS)
        self.assertIn('Unpublished 1 result(s).', str(second_messages[-1]))
        self.result.refresh_from_db()
        self.assertFalse(self.result.is_published)

    def test_admin_validation_error_is_a_message_not_an_exception(self):
        model_admin = ExamAdmin(Exam, admin.site)
        request = self.admin_request()
        model_admin.publish_selected_results(
            request, model_admin.get_queryset(request).filter(pk=self.exam.pk),
        )
        stored = list(get_messages(request))
        self.assertEqual(stored[-1].level, messages.ERROR)
        self.assertIn('no approved results', str(stored[-1]).lower())

    def test_admin_multi_exam_failure_rolls_back(self):
        self.approve()
        exam_two, _ = self.make_exam('Admin invalid exam')
        model_admin = ExamAdmin(Exam, admin.site)
        request = self.admin_request()
        model_admin.publish_selected_results(
            request,
            model_admin.get_queryset(request).filter(
                pk__in=[self.exam.pk, exam_two.pk],
            ),
        )
        self.result.refresh_from_db()
        self.assertFalse(self.result.is_published)
        self.assertEqual(list(get_messages(request))[-1].level, messages.ERROR)

    def test_school_admin_cannot_action_other_school_exam(self):
        model_admin = ExamAdmin(Exam, admin.site)
        request = self.admin_request()
        model_admin.publish_selected_results(
            request, Exam.objects.filter(pk=self.other_exam.pk),
        )
        stored = list(get_messages(request))
        self.assertEqual(stored[-1].level, messages.ERROR)
        self.assertIn('No permitted exams', str(stored[-1]))
        self.other_result.refresh_from_db()
        self.assertFalse(self.other_result.is_published)

    def test_database_rejects_published_without_metadata(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            ExamResult.objects.filter(pk=self.result.pk).update(is_published=True)

    def test_database_rejects_unpublished_with_metadata(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            ExamResult.objects.filter(pk=self.result.pk).update(
                is_published=False,
                published_by=self.admin_user,
                published_at=timezone.now(),
            )

    def test_database_rejects_nonapproved_published_result(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            ExamResult.objects.filter(pk=self.result.pk).update(
                is_published=True,
                published_by=self.admin_user,
                published_at=timezone.now(),
                workflow_status='draft',
            )

    @override_settings(TRUST_X_FORWARDED_FOR=False)
    def test_audit_ip_defaults_to_remote_addr(self):
        request = RequestFactory().post(
            '/', REMOTE_ADDR='192.0.2.10',
            HTTP_X_FORWARDED_FOR='198.51.100.2',
        )
        self.assertEqual(request_audit_metadata(request)['ip_address'], '192.0.2.10')

    @override_settings(TRUST_X_FORWARDED_FOR=True)
    def test_audit_ip_uses_first_valid_forwarded_address_when_trusted(self):
        request = RequestFactory().post(
            '/', REMOTE_ADDR='192.0.2.10',
            HTTP_X_FORWARDED_FOR='invalid, 198.51.100.2, 203.0.113.3',
        )
        self.assertEqual(request_audit_metadata(request)['ip_address'], '198.51.100.2')

    @override_settings(TRUST_X_FORWARDED_FOR=True)
    def test_invalid_forwarded_ip_falls_back_to_remote_addr(self):
        request = RequestFactory().post(
            '/', REMOTE_ADDR='192.0.2.20', HTTP_X_FORWARDED_FOR='bad, worse',
        )
        self.assertEqual(request_audit_metadata(request)['ip_address'], '192.0.2.20')

    @override_settings(TRUST_X_FORWARDED_FOR=True)
    def test_invalid_audit_ips_are_handled_safely(self):
        request = RequestFactory().post(
            '/', REMOTE_ADDR='invalid', HTTP_X_FORWARDED_FOR='bad, worse',
        )
        self.assertIsNone(request_audit_metadata(request)['ip_address'])

    def test_published_result_list_query_count_remains_bounded(self):
        self.approve()
        self.result.is_published = True
        self.result.published_by = self.admin_user
        self.result.published_at = timezone.now()
        self.result.save()
        self.auth(self.admin_user)
        with self.assertNumQueries(2):
            response = self.client.get('/api/v1/exam-results/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 1)
