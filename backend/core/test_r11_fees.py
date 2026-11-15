"""Release 1.1: school fees (admin issue/pay/void, parent view, reminders, isolation)."""

from datetime import date, timedelta
from decimal import Decimal

from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from core.models import (
    AcademicYear, Classroom, FeeCategory, FeePayment, Notification, Parent, School, SchoolMembership,
    Section, Student, StudentEnrollment, StudentFee, StudentGuardian, User,
)
from core.services import fees as fee_service


class FeeFixture(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.today = timezone.localdate()
        self.school, self.year, self.classroom, self.section = self.build_school('FEE')
        self.other_school, self.other_year, _, _ = self.build_school('FEX')
        self.admin, self.admin_m = self.user('fee-admin', 'school_admin', self.school)
        self.other_admin, self.other_admin_m = self.user('fex-admin', 'school_admin', self.other_school)
        self.students = [self.student(f'طالب {i}', self.school, self.year, self.classroom, self.section)
                         for i in range(3)]
        self.other_student = self.student('طالب آخر', self.other_school, self.other_year,
                                          *self.first_class(self.other_school))
        self.category = FeeCategory.objects.create(school=self.school, name='رسوم دراسية')
        self.other_category = FeeCategory.objects.create(school=self.other_school, name='رسوم دراسية')
        self.parent_user, self.parent_m = self.user('fee-parent', 'parent', self.school)
        self.parent = Parent.objects.create(school=self.school, user=self.parent_user, full_name='ولي أمر')
        self.guardian = StudentGuardian.objects.create(
            student=self.students[0], parent=self.parent, relationship='father', is_primary=True,
        )

    def build_school(self, code):
        school = School.objects.create(name=f'School {code}', code=code)
        year = AcademicYear.objects.create(
            school=school, name='2026/2027', start_date=date(2026, 8, 1), end_date=date(2027, 6, 30), is_active=True,
        )
        classroom = Classroom.objects.create(school=school, academic_year=year, name='الأول', code='G1')
        section = Section.objects.create(school=school, academic_year=year, classroom=classroom, name='أ', code='A')
        return school, year, classroom, section

    def first_class(self, school):
        classroom = Classroom.objects.filter(school=school).first()
        return classroom, Section.objects.filter(classroom=classroom).first()

    def user(self, username, role, school):
        user = User.objects.create_user(username=username, password='pass-12345', school=school, role=role)
        membership, _ = SchoolMembership.objects.get_or_create(
            user=user, school=school, role=role, defaults={'status': 'active', 'is_default': True},
        )
        return user, membership

    def student(self, name, school, year, classroom, section):
        student = Student.objects.create(school=school, full_name=name, gender='male')
        StudentEnrollment.objects.create(
            student=student, school=school, academic_year=year, classroom=classroom, section=section,
            is_current=True, status='active',
        )
        return student

    def headers(self, user, membership):
        return {
            'HTTP_AUTHORIZATION': f'Bearer {RefreshToken.for_user(user).access_token}',
            'HTTP_X_SCHOOL_MEMBERSHIP_ID': str(membership.id),
        }

    def admin_headers(self):
        return self.headers(self.admin, self.admin_m)

    def issue(self, confirm=True, **overrides):
        payload = {
            'category_id': self.category.id, 'title': 'الرسوم الدراسية', 'amount': '300000',
            'installments': [
                {'amount': '100000', 'due_date': (self.today + timedelta(days=10)).isoformat()},
                {'amount': '200000', 'due_date': (self.today + timedelta(days=60)).isoformat()},
            ],
            'scope': 'school', 'confirm': confirm, **overrides,
        }
        return self.client.post('/api/v1/admin/fees/issue/', payload, format='json', **self.admin_headers())


class FeeIssueTests(FeeFixture):
    def test_preview_creates_nothing_and_confirm_creates_installments(self):
        preview = self.issue(confirm=False)
        self.assertEqual(preview.status_code, 200, preview.content)
        self.assertEqual(preview.json()['student_count'], 3)
        self.assertEqual(preview.json()['total_net'], '900000.00')
        self.assertEqual(StudentFee.objects.count(), 0)
        done = self.issue()
        self.assertEqual(done.status_code, 201, done.content)
        self.assertEqual(done.json()['created'], 6)
        fees = StudentFee.objects.filter(student=self.students[0]).order_by('installment_number')
        self.assertEqual([f.amount for f in fees], [Decimal('100000.00'), Decimal('200000.00')])
        self.assertEqual(fees[1].title, 'الرسوم الدراسية - القسط 2')
        self.assertFalse(StudentFee.objects.filter(student=self.other_student).exists())

    def test_discount_applies_to_earliest_installments(self):
        self.issue(discount='150000', scope='students', student_ids=[self.students[1].id])
        fees = list(StudentFee.objects.filter(student=self.students[1]).order_by('installment_number'))
        self.assertEqual([f.discount for f in fees], [Decimal('100000.00'), Decimal('50000.00')])
        self.assertEqual(fees[0].payment_state(), 'paid')

    def test_scope_section_and_validation_errors(self):
        self.assertEqual(self.issue(scope='section', section_id=self.section.id).json()['created'], 6)
        bad = [
            {'installments': [{'amount': '1', 'due_date': self.today.isoformat()}]},  # sum mismatch
            {'category_id': self.other_category.id},  # other school category
            {'scope': 'students', 'student_ids': [self.other_student.id]},  # other school student
            {'amount': '0'},
            {'discount': '400000'},
            {'scope': 'classroom'},
        ]
        for overrides in bad:
            response = self.issue(confirm=False, **overrides)
            self.assertEqual(response.status_code, 400, overrides)

    def test_issue_notifies_financial_guardians_only(self):
        other_parent_user, other_parent_m = self.user('fee-parent-2', 'parent', self.school)
        other_parent = Parent.objects.create(school=self.school, user=other_parent_user, full_name='أم')
        StudentGuardian.objects.create(
            student=self.students[0], parent=other_parent, relationship='mother', can_receive_financial_alerts=False,
        )
        with self.captureOnCommitCallbacks(execute=True):
            self.issue()
        self.assertEqual(Notification.objects.filter(recipient_membership=self.parent_m, notification_type='fee_issued').count(), 1)
        self.assertFalse(Notification.objects.filter(recipient_membership=other_parent_m).exists())

    def test_role_and_historical_gates(self):
        teacher, teacher_m = self.user('fee-teacher', 'teacher', self.school)
        response = self.client.post('/api/v1/admin/fees/issue/', {}, format='json', **self.headers(teacher, teacher_m))
        self.assertEqual(response.status_code, 403)
        self.admin_m.status = 'historical'
        self.admin_m.is_default = False
        self.admin_m.save()
        self.assertEqual(self.issue().status_code, 403)
        self.assertEqual(self.client.get('/api/v1/admin/fees/', **self.admin_headers()).status_code, 200)


class FeePaymentTests(FeeFixture):
    def setUp(self):
        super().setUp()
        self.issue()
        self.fee = StudentFee.objects.get(student=self.students[0], installment_number=1)

    def pay(self, fee=None, amount='40000', headers=None, **extra):
        fee = fee or self.fee
        return self.client.post(f'/api/v1/admin/fees/{fee.id}/payments/', {
            'amount': amount, 'method': 'cash', **extra,
        }, format='json', **(headers or self.admin_headers()))

    def test_partial_then_full_payment_with_sequential_receipts(self):
        first = self.pay()
        self.assertEqual(first.status_code, 201, first.content)
        self.assertEqual(first.json()['receipt_number'], f'R{self.today.year}-000001')
        self.fee.refresh_from_db()
        self.assertEqual(self.fee.payment_state(), 'partial')
        second = self.pay(amount='60000')
        self.assertEqual(second.json()['receipt_number'], f'R{self.today.year}-000002')
        self.fee.refresh_from_db()
        self.assertEqual(self.fee.payment_state(), 'paid')
        self.assertEqual(self.pay(amount='1').status_code, 400)  # nothing left

    def test_overpayment_future_date_and_cancelled_fee_rejected(self):
        self.assertEqual(self.pay(amount='100001').status_code, 400)
        future = (self.today + timedelta(days=1)).isoformat()
        self.assertEqual(self.pay(paid_on=future).status_code, 400)
        other = StudentFee.objects.get(student=self.students[1], installment_number=1)
        url = f'/api/v1/admin/fees/{other.id}/cancel/'
        self.assertEqual(self.client.post(url, {'reason': 'خطأ'}, format='json', **self.admin_headers()).status_code, 200)
        self.assertEqual(self.pay(fee=other).status_code, 400)

    def test_void_restores_balance_and_cancel_requires_no_payments(self):
        payment_id = self.pay().json()['id']
        cancel = self.client.post(f'/api/v1/admin/fees/{self.fee.id}/cancel/', {'reason': 'x'}, format='json',
                                  **self.admin_headers())
        self.assertEqual(cancel.status_code, 400)
        void = self.client.post(f'/api/v1/admin/fees/payments/{payment_id}/void/', {'reason': 'إدخال خاطئ'},
                                format='json', **self.admin_headers())
        self.assertEqual(void.status_code, 200)
        self.fee.refresh_from_db()
        self.assertEqual(self.fee.paid_amount, Decimal('0.00'))
        again = self.client.post(f'/api/v1/admin/fees/payments/{payment_id}/void/', {'reason': 'x'}, format='json',
                                 **self.admin_headers())
        self.assertEqual(again.status_code, 400)

    def test_payment_notifies_guardian_with_receipt(self):
        with self.captureOnCommitCallbacks(execute=True):
            receipt = self.pay().json()['receipt_number']
        note = Notification.objects.get(recipient_membership=self.parent_m, notification_type='payment_received')
        self.assertIn(receipt, note.body)

    def test_other_school_cannot_touch_fee_or_payment(self):
        other = self.headers(self.other_admin, self.other_admin_m)
        self.assertEqual(self.pay(headers=other).status_code, 404)
        self.assertEqual(self.client.get(f'/api/v1/admin/fees/{self.fee.id}/', **other).status_code, 404)
        payment_id = self.pay().json()['id']
        void = self.client.post(f'/api/v1/admin/fees/payments/{payment_id}/void/', {'reason': 'x'}, format='json', **other)
        self.assertEqual(void.status_code, 404)
        listing = self.client.get('/api/v1/admin/fees/', **other).json()
        self.assertEqual(listing['count'], 0)
        self.assertEqual(self.client.get('/api/v1/admin/fees/payments/', **other).json()['count'], 0)

    def test_list_filters_summary_and_detail(self):
        self.pay(amount='100000')
        response = self.client.get('/api/v1/admin/fees/', {'state': 'paid'}, **self.admin_headers())
        self.assertEqual(response.json()['count'], 1)
        response = self.client.get('/api/v1/admin/fees/', {'student_id': self.students[0].id}, **self.admin_headers())
        self.assertEqual(response.json()['count'], 2)
        self.assertEqual(response.json()['summary']['paid'], '100000.00')
        self.assertEqual(self.client.get('/api/v1/admin/fees/', {'state': 'bogus'}, **self.admin_headers()).status_code, 400)
        summary = self.client.get('/api/v1/admin/fees/summary/', **self.admin_headers()).json()
        self.assertEqual(summary['total'], '900000.00')
        self.assertEqual(summary['remaining'], '800000.00')
        self.assertEqual(summary['collected_this_month'], '100000.00')
        detail = self.client.get(f'/api/v1/admin/fees/{self.fee.id}/', **self.admin_headers()).json()
        self.assertEqual(len(detail['payments']), 1)

    def test_overdue_state_and_reminders_are_idempotent(self):
        StudentFee.objects.filter(pk=self.fee.pk).update(due_date=self.today - timedelta(days=2))
        due_soon = StudentFee.objects.get(student=self.students[0], installment_number=2)
        StudentFee.objects.filter(pk=due_soon.pk).update(due_date=self.today + timedelta(days=3))
        self.assertEqual(self.client.get('/api/v1/admin/fees/', {'state': 'overdue'}, **self.admin_headers()).json()['count'], 1)
        call_command('run_billing_jobs', stdout=open('nul' if __import__('os').name == 'nt' else '/dev/null', 'w'))
        fee_service.send_due_reminders()
        kinds = list(Notification.objects.filter(recipient_membership=self.parent_m).values_list('notification_type', flat=True))
        self.assertEqual(sorted(kinds), ['fee_due', 'fee_overdue'])


class ParentFeeTests(FeeFixture):
    def setUp(self):
        super().setUp()
        self.issue()
        fee = StudentFee.objects.get(student=self.students[0], installment_number=1)
        fee_service.record_payment(school=self.school, fee_id=fee.id, actor=self.admin, amount='25000',
                                   method='bank_transfer', paid_on=self.today)

    def test_parent_sees_own_child_summary_fees_and_receipts(self):
        response = self.client.get(f'/api/v1/parents/me/children/{self.students[0].id}/fees/',
                                   **self.headers(self.parent_user, self.parent_m))
        self.assertEqual(response.status_code, 200, response.content)
        body = response.json()
        self.assertEqual(body['summary']['total'], '300000.00')
        self.assertEqual(body['summary']['paid'], '25000.00')
        self.assertEqual(len(body['fees']), 2)
        self.assertEqual(len(body['payments']), 1)
        overview = self.client.get('/api/v1/parents/me/fees/', **self.headers(self.parent_user, self.parent_m)).json()
        self.assertEqual([c['student_id'] for c in overview['children']], [self.students[0].id])

    def test_parent_cannot_see_unlinked_or_other_school_child(self):
        headers = self.headers(self.parent_user, self.parent_m)
        for student in (self.students[1], self.other_student):
            response = self.client.get(f'/api/v1/parents/me/children/{student.id}/fees/', **headers)
            self.assertEqual(response.status_code, 404)

    def test_guardian_without_financial_permission_gets_404(self):
        self.guardian.can_receive_financial_alerts = False
        self.guardian.save()
        response = self.client.get(f'/api/v1/parents/me/children/{self.students[0].id}/fees/',
                                   **self.headers(self.parent_user, self.parent_m))
        self.assertEqual(response.status_code, 404)

    def test_student_and_teacher_cannot_use_parent_fee_endpoints(self):
        teacher, teacher_m = self.user('fee-teacher', 'teacher', self.school)
        response = self.client.get(f'/api/v1/parents/me/children/{self.students[0].id}/fees/',
                                   **self.headers(teacher, teacher_m))
        self.assertEqual(response.status_code, 403)

    def test_void_payment_hidden_from_parent(self):
        payment = FeePayment.objects.get()
        fee_service.void_payment(school=self.school, payment_id=payment.id, actor=self.admin, reason='خطأ')
        body = self.client.get(f'/api/v1/parents/me/children/{self.students[0].id}/fees/',
                               **self.headers(self.parent_user, self.parent_m)).json()
        self.assertEqual(body['payments'], [])
        self.assertEqual(body['summary']['paid'], '0.00')


class ParentCodeRegressionTests(FeeFixture):
    def test_second_parent_in_school_gets_next_code(self):
        second = Parent.objects.create(school=self.school, full_name='ولي أمر ثان')
        self.assertEqual(self.parent.parent_code, 'FEE-P00001')
        self.assertEqual(second.parent_code, 'FEE-P00002')


class FeeCategoryTests(FeeFixture):
    def test_categories_are_school_scoped_and_unique(self):
        headers = self.admin_headers()
        created = self.client.post('/api/v1/admin/fees/categories/', {'name': 'النقل'}, format='json', **headers)
        self.assertEqual(created.status_code, 201)
        dup = self.client.post('/api/v1/admin/fees/categories/', {'name': 'النقل'}, format='json', **headers)
        self.assertEqual(dup.status_code, 400)
        names = [c['name'] for c in self.client.get('/api/v1/admin/fees/categories/', **headers).json()]
        self.assertEqual(sorted(names), ['النقل', 'رسوم دراسية'])
        other = self.headers(self.other_admin, self.other_admin_m)
        patch = self.client.patch(f'/api/v1/admin/fees/categories/{created.json()["id"]}/', {'name': 'x'},
                                  format='json', **other)
        self.assertEqual(patch.status_code, 404)
