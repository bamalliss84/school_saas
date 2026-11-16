"""Optional error alerts by email: off by default, privacy-safe, throttled."""

import logging
from unittest import mock

from django.core import mail
from django.core.cache import cache
from django.core.management import call_command
from django.test import RequestFactory, SimpleTestCase, TestCase, override_settings
from rest_framework.permissions import AllowAny
from rest_framework.test import APIRequestFactory
from rest_framework.views import APIView

from core.monitoring import ErrorAlertEmailHandler

SECRET_MESSAGE = 'student Ahmed national id 778899'


def _log_request_error(path='/api/v1/students/5/?name=Ahmed', message=SECRET_MESSAGE):
    request = RequestFactory().post(path, data={'full_name': 'Ahmed'}, HTTP_AUTHORIZATION='Bearer tok-123')
    try:
        raise ValueError(message)
    except ValueError:
        logging.getLogger('django.request').error(
            'Internal Server Error: %s', request.path, exc_info=True,
            extra={'request': request, 'status_code': 500},
        )


class ErrorAlertTests(SimpleTestCase):
    def setUp(self):
        cache.clear()

    def test_disabled_without_recipients(self):
        with override_settings(ERROR_ALERT_EMAILS=[]):
            _log_request_error()
        self.assertEqual(mail.outbox, [])

    @override_settings(ERROR_ALERT_EMAILS=['ops@example.com'], ERROR_ALERT_THROTTLE_SECONDS=600)
    def test_server_error_sends_alert_without_personal_data(self):
        _log_request_error()
        self.assertEqual(len(mail.outbox), 1)
        alert = mail.outbox[0]
        self.assertEqual(alert.to, ['ops@example.com'])
        text = alert.subject + '\n' + alert.body
        self.assertIn('ValueError', alert.subject)
        self.assertIn('POST /api/v1/students/5/', text)
        self.assertIn('test_r11_monitoring.py', alert.body)  # the stack frames point at the code
        self.assertIn('Status: 500', alert.body)
        for leaked in ('Ahmed', '778899', 'tok-123', 'name=', 'full_name', 'Bearer'):
            self.assertNotIn(leaked, text)

    @override_settings(ERROR_ALERT_EMAILS=['ops@example.com'], ERROR_ALERT_THROTTLE_SECONDS=600)
    def test_same_error_is_throttled(self):
        _log_request_error(path='/api/v1/a/')
        _log_request_error(path='/api/v1/a/')
        self.assertEqual(len(mail.outbox), 1)

    @override_settings(ERROR_ALERT_EMAILS=['ops@example.com'], ERROR_ALERT_THROTTLE_SECONDS=0)
    def test_throttle_can_be_disabled(self):
        _log_request_error()
        _log_request_error()
        self.assertEqual(len(mail.outbox), 2)

    @override_settings(ERROR_ALERT_EMAILS=['ops@example.com'])
    def test_warnings_and_client_errors_do_not_alert(self):
        logging.getLogger('django.request').warning('Not Found: /x/')
        logging.getLogger('core').info('ordinary event')
        self.assertEqual(mail.outbox, [])

    @override_settings(ERROR_ALERT_EMAILS=['ops@example.com'])
    def test_a_failing_mail_server_never_breaks_the_caller(self):
        handler = ErrorAlertEmailHandler()
        record = logging.LogRecord('core', logging.ERROR, __file__, 1, 'boom', None, None)
        with mock.patch('core.monitoring.send_mail', side_effect=OSError('smtp down')), \
                mock.patch.object(handler, 'handleError') as handle_error:
            handler.emit(record)  # must not raise
        handle_error.assert_called_once()


class _BrokenView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request):
        raise ValueError(SECRET_MESSAGE)


@override_settings(ERROR_ALERT_EMAILS=['ops@example.com'])
class ApiErrorAlertTests(SimpleTestCase):
    def setUp(self):
        cache.clear()

    def test_unhandled_api_error_sends_one_alert_with_the_path(self):
        response = _BrokenView.as_view()(APIRequestFactory().get('/api/v1/broken/?q=Ahmed'))
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.data['message'], 'Internal server error.')
        # Django's own 5xx response log line (no stack) must not send a second alert.
        logging.getLogger('django.request').error('Internal Server Error: /api/v1/broken/',
                                                  extra={'status_code': 500})
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('GET /api/v1/broken/', mail.outbox[0].subject)
        self.assertNotIn('Ahmed', mail.outbox[0].subject + mail.outbox[0].body)


class BillingJobAlertTests(TestCase):
    def setUp(self):
        cache.clear()

    @override_settings(ERROR_ALERT_EMAILS=['ops@example.com'])
    def test_failed_billing_job_is_logged_alerted_and_still_fails(self):
        # No assertLogs here: it would swallow the record before the alert handler on "core".
        with mock.patch('core.services.fees.send_due_reminders', side_effect=RuntimeError(SECRET_MESSAGE)):
            with self.assertRaises(RuntimeError):
                call_command('run_billing_jobs')
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('RuntimeError', mail.outbox[0].subject)
        self.assertNotIn('778899', mail.outbox[0].body)

    def test_billing_job_succeeds_without_alerts(self):
        call_command('run_billing_jobs', stdout=mock.MagicMock())
        self.assertEqual(mail.outbox, [])
