"""Release 1.1: platform plans, school subscriptions, invoices and payments."""

from datetime import timedelta
from decimal import Decimal

from django.db import IntegrityError, transaction
from django.utils import timezone
from rest_framework_simplejwt.tokens import RefreshToken

from core.models import Notification, PlatformInvoice, SchoolSubscription, SubscriptionPlan, User
from core.services import subscriptions as subscription_service
from core.test_r11_fees import FeeFixture


class SubscriptionFixture(FeeFixture):
    def setUp(self):
        super().setUp()
        self.owner = User.objects.create_user(username='platform-owner', password='pass-12345', role='super_admin')
        self.plan = SubscriptionPlan.objects.create(
            code='standard', name='القياسية', base_price=Decimal('100000'), price_per_student=Decimal('5000'),
            max_students=500, features=['الحضور', 'الواجبات', 'الرسوم'],
        )

    def owner_headers(self):
        return {'HTTP_AUTHORIZATION': f'Bearer {RefreshToken.for_user(self.owner).access_token}'}

    def subscribe(self, school=None, status='active', **extra):
        payload = {
            'school': (school or self.school).id, 'plan': self.plan.id, 'status': status,
            'start_date': self.today.isoformat(), 'end_date': (self.today + timedelta(days=365)).isoformat(), **extra,
        }
        return self.client.post('/api/v1/platform/subscriptions/', payload, format='json', **self.owner_headers())


class PlatformOwnerTests(SubscriptionFixture):
    def test_only_platform_owner_reaches_platform_endpoints(self):
        self.assertEqual(self.client.get('/api/v1/platform/summary/', **self.owner_headers()).status_code, 200)
        for headers in (self.admin_headers(), self.headers(self.parent_user, self.parent_m)):
            for url in ('/api/v1/platform/summary/', '/api/v1/platform/plans/', '/api/v1/platform/schools/'):
                self.assertEqual(self.client.get(url, **headers).status_code, 403, url)
        self.assertIn(self.client.get('/api/v1/platform/summary/').status_code, (401, 403))

    def test_plan_crud_and_validation(self):
        created = self.client.post('/api/v1/platform/plans/', {
            'code': 'premium', 'name': 'المتقدمة', 'price_per_student': '8000', 'features': ['كل شيء'],
        }, format='json', **self.owner_headers())
        self.assertEqual(created.status_code, 201, created.content)
        bad = self.client.post('/api/v1/platform/plans/', {'code': 'x', 'name': 'x', 'features': [1, 2]},
                               format='json', **self.owner_headers())
        self.assertEqual(bad.status_code, 400)
        patched = self.client.patch(f'/api/v1/platform/plans/{created.json()["id"]}/', {'is_active': False},
                                    format='json', **self.owner_headers())
        self.assertFalse(patched.json()['is_active'])

    def test_subscribe_renew_keeps_history_and_single_current(self):
        first = self.subscribe(status='trial')
        self.assertEqual(first.status_code, 201, first.content)
        second = self.subscribe()
        self.assertEqual(second.status_code, 201)
        statuses = sorted(SchoolSubscription.objects.filter(school=self.school).values_list('status', flat=True))
        self.assertEqual(statuses, ['active', 'cancelled'])
        with self.assertRaises(IntegrityError), transaction.atomic():
            SchoolSubscription.objects.create(
                school=self.school, plan=self.plan, status='trial', start_date=self.today, end_date=self.today,
            )

    def test_status_transitions_are_enforced(self):
        sub_id = self.subscribe().json()['id']
        url = f'/api/v1/platform/subscriptions/{sub_id}/'
        ok = self.client.patch(url, {'status': 'suspended'}, format='json', **self.owner_headers())
        self.assertEqual(ok.status_code, 200)
        bad = self.client.patch(url, {'status': 'trial'}, format='json', **self.owner_headers())
        self.assertEqual(bad.status_code, 400)
        locked = self.client.patch(url, {'school': self.other_school.id}, format='json', **self.owner_headers())
        self.assertEqual(locked.status_code, 400)

    def test_invoice_amount_payment_and_reactivation(self):
        sub_id = self.subscribe().json()['id']
        with self.captureOnCommitCallbacks(execute=True):
            invoice = self.client.post('/api/v1/platform/invoices/', {
                'subscription_id': sub_id, 'period_start': self.today.isoformat(),
                'period_end': (self.today + timedelta(days=364)).isoformat(),
                'due_date': (self.today + timedelta(days=14)).isoformat(),
            }, format='json', **self.owner_headers())
        self.assertEqual(invoice.status_code, 201, invoice.content)
        body = invoice.json()
        # 3 active students: 100000 + 3 * 5000
        self.assertEqual(body['amount'], '115000.00')
        self.assertTrue(body['number'].startswith(f'INV{self.today.year}-'))
        self.assertTrue(Notification.objects.filter(recipient_membership=self.admin_m,
                                                    notification_type='subscription').exists())
        url = f'/api/v1/platform/invoices/{body["id"]}/payments/'
        too_much = self.client.post(url, {'amount': '200000', 'method': 'bank_transfer'}, format='json',
                                    **self.owner_headers())
        self.assertEqual(too_much.status_code, 400)
        SchoolSubscription.objects.filter(pk=sub_id).update(status='past_due')
        paid = self.client.post(url, {'amount': '115000', 'method': 'bank_transfer', 'reference': 'TRX-1'},
                                format='json', **self.owner_headers())
        self.assertEqual(paid.json()['status'], 'paid')
        self.assertEqual(SchoolSubscription.objects.get(pk=sub_id).status, 'active')
        void = self.client.post(f'/api/v1/platform/invoices/{body["id"]}/void/', {'reason': 'x'}, format='json',
                                **self.owner_headers())
        self.assertEqual(void.status_code, 400)

    def test_overdue_job_marks_past_due_and_summary_counts(self):
        subscription = SchoolSubscription.objects.get(pk=self.subscribe().json()['id'])
        invoice = subscription_service.issue_invoice(
            subscription_id=subscription.id, period_start=self.today, period_end=self.today + timedelta(days=30),
            due_date=self.today,
        )
        PlatformInvoice.objects.filter(pk=invoice.pk).update(due_date=self.today - timedelta(days=1))
        self.assertEqual(subscription_service.mark_overdue_subscriptions(), 1)
        subscription.refresh_from_db()
        self.assertEqual(subscription.status, 'past_due')
        summary = self.client.get('/api/v1/platform/summary/', **self.owner_headers()).json()
        self.assertEqual(summary['subscriptions']['past_due'], 1)
        self.assertEqual(summary['schools_without_subscription'], 1)
        self.assertEqual(Decimal(summary['overdue']), invoice.amount)
        schools = self.client.get('/api/v1/platform/schools/', {'warning': 'past_due'}, **self.owner_headers()).json()
        self.assertEqual([row['school_id'] for row in schools['results']], [self.school.id])


class SchoolAdminSubscriptionViewTests(SubscriptionFixture):
    def test_school_admin_sees_only_own_status_and_invoices(self):
        sub_id = self.subscribe().json()['id']
        subscription_service.issue_invoice(
            subscription_id=sub_id, period_start=self.today, period_end=self.today + timedelta(days=30),
            due_date=self.today + timedelta(days=7),
        )
        mine = self.client.get('/api/v1/admin/subscription/', **self.admin_headers()).json()
        self.assertTrue(mine['has_subscription'])
        self.assertEqual(mine['plan']['code'], 'standard')
        self.assertEqual(mine['student_count'], 3)
        self.assertEqual(len(mine['invoices']), 1)
        other = self.client.get('/api/v1/admin/subscription/', **self.headers(self.other_admin, self.other_admin_m)).json()
        self.assertFalse(other['has_subscription'])
        self.assertEqual(other['warning'], 'no_subscription')
        self.assertEqual(other['invoices'], [])

    def test_expiry_and_limit_warnings(self):
        self.subscribe(end_date=(self.today + timedelta(days=10)).isoformat())
        self.assertEqual(subscription_service.school_subscription_status(self.school)['warning'], 'expiring')
        sub = SchoolSubscription.objects.get(school=self.school, status='active')
        sub.end_date = self.today + timedelta(days=200)
        sub.student_limit = 2
        sub.save()
        self.assertEqual(subscription_service.school_subscription_status(self.school)['warning'], 'over_limit')

    def test_teacher_cannot_read_subscription(self):
        teacher, teacher_m = self.user('sub-teacher', 'teacher', self.school)
        self.assertEqual(self.client.get('/api/v1/admin/subscription/', **self.headers(teacher, teacher_m)).status_code, 403)

    def test_historical_admin_can_read(self):
        self.admin_m.status = 'historical'
        self.admin_m.is_default = False
        self.admin_m.save()
        self.assertEqual(self.client.get('/api/v1/admin/subscription/', **self.admin_headers()).status_code, 200)
        self.assertEqual(timezone.localdate(), self.today)
