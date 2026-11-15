"""Release 1.0.1: password reset, password change and production settings guard."""

import os
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from django.core import mail
from django.test import TestCase, override_settings
from rest_framework.test import APIClient
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken
from rest_framework_simplejwt.tokens import RefreshToken

from core.models import AcademicYear, School, SchoolMembership, User

STRONG = 'N3w-Strong-Passphrase!'


@override_settings(
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
    PASSWORD_RESET_URL='https://portal.example.test/reset-password',
)
class PasswordResetTests(TestCase):
    def setUp(self):
        self.school = School.objects.create(name='R101 School', code='R101')
        self.year = AcademicYear.objects.create(
            school=self.school, name='2026/2027', start_date='2026-08-01',
            end_date='2027-06-30', is_active=True,
        )
        self.user = User.objects.create_user(
            username='r101-admin', password='old-pass-1234', email='admin@example.test',
            school=self.school, academic_year=self.year, role='school_admin',
        )
        self.membership = SchoolMembership.objects.create(
            user=self.user, school=self.school, role='school_admin', status='active', is_default=True,
        )
        self.client = APIClient()

    def request_reset(self, identifier):
        return self.client.post('/api/v1/auth/password/reset/', {'identifier': identifier}, format='json')

    def link_params(self):
        url = re.search(r'https://portal\.example\.test/reset-password\?\S+', mail.outbox[-1].body).group(0)
        query = parse_qs(urlparse(url).query)
        return query['uid'][0], query['token'][0]

    def test_reset_by_username_and_email_sends_link(self):
        for identifier in ('r101-admin', 'ADMIN@example.test'):
            response = self.request_reset(identifier)
            self.assertEqual(response.status_code, 200)
        self.assertEqual(len(mail.outbox), 2)
        self.assertEqual(mail.outbox[0].to, ['admin@example.test'])
        self.assertIn('reset-password?uid=', mail.outbox[0].body)

    def test_unknown_inactive_or_emailless_accounts_get_same_response_and_no_email(self):
        known = self.request_reset('r101-admin').json()
        mail.outbox.clear()
        User.objects.create_user(username='no-email', password='x-pass-1234', school=self.school)
        User.objects.create_user(
            username='gone', password='x-pass-1234', email='gone@example.test', is_active=False, school=self.school,
        )
        for identifier in ('nobody', 'no-email', 'gone', 'gone@example.test'):
            response = self.request_reset(identifier)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json(), known)
        self.assertEqual(mail.outbox, [])

    def test_shared_email_is_ambiguous_and_sends_nothing(self):
        User.objects.create_user(
            username='twin', password='x-pass-1234', email='admin@example.test', school=self.school,
        )
        self.request_reset('admin@example.test')
        self.assertEqual(mail.outbox, [])

    def test_confirm_sets_password_and_revokes_sessions(self):
        refresh = RefreshToken.for_user(self.user)
        self.request_reset('r101-admin')
        uid, token = self.link_params()
        response = self.client.post('/api/v1/auth/password/reset/confirm/', {
            'uid': uid, 'token': token, 'new_password': STRONG,
        }, format='json')
        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password(STRONG))
        self.assertTrue(BlacklistedToken.objects.filter(token__jti=refresh['jti']).exists())
        login = self.client.post('/api/v1/auth/login/', {'username': 'r101-admin', 'password': STRONG}, format='json')
        self.assertEqual(login.status_code, 200)

    def test_link_is_single_use(self):
        self.request_reset('r101-admin')
        uid, token = self.link_params()
        payload = {'uid': uid, 'token': token, 'new_password': STRONG}
        self.assertEqual(self.client.post('/api/v1/auth/password/reset/confirm/', payload, format='json').status_code, 200)
        payload['new_password'] = STRONG + 'x'
        again = self.client.post('/api/v1/auth/password/reset/confirm/', payload, format='json')
        self.assertEqual(again.status_code, 400)

    def test_bad_token_uid_and_weak_password_are_rejected(self):
        self.request_reset('r101-admin')
        uid, token = self.link_params()
        cases = [
            {'uid': uid, 'token': 'bad-token', 'new_password': STRONG},
            {'uid': 'bm9wZQ', 'token': token, 'new_password': STRONG},
            {'uid': uid, 'token': token, 'new_password': '123'},
        ]
        for payload in cases:
            response = self.client.post('/api/v1/auth/password/reset/confirm/', payload, format='json')
            self.assertEqual(response.status_code, 400, payload)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('old-pass-1234'))

    def test_expired_bearer_token_does_not_block_anonymous_reset(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer not-a-valid-token')
        self.assertEqual(self.request_reset('r101-admin').status_code, 200)

    def test_change_password_requires_current_password(self):
        refresh = RefreshToken.for_user(self.user)
        headers = {
            'HTTP_AUTHORIZATION': f'Bearer {refresh.access_token}',
            'HTTP_X_SCHOOL_MEMBERSHIP_ID': str(self.membership.id),
        }
        url = '/api/v1/auth/password/change/'
        wrong = self.client.post(url, {'current_password': 'nope', 'new_password': STRONG}, format='json', **headers)
        self.assertEqual(wrong.status_code, 400)
        same = self.client.post(
            url, {'current_password': 'old-pass-1234', 'new_password': 'old-pass-1234'}, format='json', **headers,
        )
        self.assertEqual(same.status_code, 400)
        ok = self.client.post(url, {'current_password': 'old-pass-1234', 'new_password': STRONG}, format='json', **headers)
        self.assertEqual(ok.status_code, 200)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password(STRONG))
        self.assertTrue(BlacklistedToken.objects.filter(token__jti=refresh['jti']).exists())

    def test_change_password_allowed_in_historical_context_and_requires_auth(self):
        self.membership.status = 'historical'
        self.membership.is_default = False
        self.membership.save()
        headers = {
            'HTTP_AUTHORIZATION': f'Bearer {RefreshToken.for_user(self.user).access_token}',
            'HTTP_X_SCHOOL_MEMBERSHIP_ID': str(self.membership.id),
        }
        payload = {'current_password': 'old-pass-1234', 'new_password': STRONG}
        self.assertIn(self.client.post('/api/v1/auth/password/change/', payload, format='json').status_code, (401, 403))
        response = self.client.post('/api/v1/auth/password/change/', payload, format='json', **headers)
        self.assertEqual(response.status_code, 200)


class ProductionSettingsGuardTests(TestCase):
    """Settings must refuse to start in production with development defaults."""

    backend_dir = Path(__file__).resolve().parent.parent

    def run_settings(self, **env):
        clean = {k: v for k, v in os.environ.items() if not k.startswith(('DJANGO_', 'POSTGRES_', 'EMAIL_'))}
        clean.update(env)
        return subprocess.run(
            [sys.executable, '-c', 'import config.settings'],
            cwd=self.backend_dir, env=clean, capture_output=True, text=True, timeout=60,
        )

    def test_production_with_defaults_fails(self):
        result = self.run_settings(DJANGO_ENV='production')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('Unsafe production settings', result.stderr)
        for name in ('DJANGO_SECRET_KEY', 'DJANGO_ALLOWED_HOSTS', 'POSTGRES_PASSWORD', 'EMAIL_BACKEND'):
            self.assertIn(name, result.stderr)

    def test_production_with_real_values_starts(self):
        result = self.run_settings(
            DJANGO_ENV='production', DJANGO_SECRET_KEY='k' * 64, DJANGO_ALLOWED_HOSTS='school.example.test',
            POSTGRES_PASSWORD='from-secret-store', EMAIL_BACKEND='django.core.mail.backends.smtp.EmailBackend',
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_development_defaults_still_start(self):
        self.assertEqual(self.run_settings().returncode, 0)
