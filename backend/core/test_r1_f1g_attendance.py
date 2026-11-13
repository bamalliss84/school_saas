"""Release 1.0 F1G — Attendance acceptance tests (docs/RELEASE1_ADMIN_F1F_F1N.md).

Verifies the admin attendance workflow on the server: tenant isolation,
role limits, historical read-only context, the daily summary used by the
Web admin screen, admin bulk recording, and the documented Super Admin scope.
"""
from datetime import date

from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from . import test_sprint3_exams
from .context import ensure_legacy_membership
from .models import Attendance, SchoolMembership

DAY = date(2026, 3, 1)


class ReleaseOneF1GAttendanceTests(APITestCase):
    password = test_sprint3_exams.SprintThreeExamPlatformTests.password
    setUpTestData = classmethod(
        test_sprint3_exams.SprintThreeExamPlatformTests.setUpTestData.__func__
    )

    def setUp(self):
        self.admin_m = ensure_legacy_membership(self.admin_user)
        self.teacher_m = ensure_legacy_membership(self.teacher_user)
        self.parent_m = ensure_legacy_membership(self.parent_user)
        self.student_m = ensure_legacy_membership(self.student_user)
        self.record = Attendance.objects.create(
            student_enrollment=self.enrollment, teacher_assignment=self.assignment,
            academic_term=self.term, attendance_date=DAY, status='present',
        )
        self.foreign = Attendance.objects.create(
            student_enrollment=self.other_enrollment, teacher_assignment=self.other_assignment,
            academic_term=self.other_term, attendance_date=DAY, status='absent',
        )

    def auth(self, user, membership):
        self.client.credentials(
            HTTP_AUTHORIZATION=f'Bearer {RefreshToken.for_user(user).access_token}',
            HTTP_X_SCHOOL_MEMBERSHIP_ID=str(membership.pk),
        )

    def bulk(self, assignment_id=None, students=None):
        return self.client.post('/api/v1/attendance/bulk/', {
            'teacher_assignment_id': assignment_id or self.assignment.pk,
            'attendance_date': DAY.isoformat(),
            'students': students or [{'student_enrollment_id': self.enrollment_two.pk, 'status': 'late'}],
        }, format='json')

    def make_historical(self):
        SchoolMembership.objects.filter(pk=self.admin_m.pk).update(status='historical', is_default=False)

    # F1G-1 + S1
    def test_admin_list_is_school_scoped_and_foreign_detail_is_404(self):
        self.auth(self.admin_user, self.admin_m)
        response = self.client.get('/api/v1/attendance/', {'attendance_date': DAY.isoformat()})
        self.assertEqual(response.status_code, 200)
        ids = [row['id'] for row in response.json()['results']]
        self.assertEqual(ids, [self.record.pk])
        self.assertEqual(self.client.get(f'/api/v1/attendance/{self.foreign.pk}/').status_code, 404)
        patch = self.client.patch(f'/api/v1/attendance/{self.foreign.pk}/', {'status': 'present'}, format='json')
        self.assertEqual(patch.status_code, 404)
        self.foreign.refresh_from_db()
        self.assertEqual(self.foreign.status, 'absent')

    # F1G-2
    def test_daily_summary_counts_only_active_school(self):
        self.auth(self.admin_user, self.admin_m)
        response = self.client.get('/api/v1/attendance/daily/', {'date': DAY.isoformat()})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual((data['total_students'], data['recorded'], data['present'], data['absent']), (2, 1, 1, 0))
        self.assertEqual(data['not_recorded'], 1)
        self.assertEqual([r['id'] for r in data['records']], [self.record.pk])

    # F1G-3
    def test_admin_corrects_status_with_validation(self):
        self.auth(self.admin_user, self.admin_m)
        ok = self.client.patch(f'/api/v1/attendance/{self.record.pk}/', {'status': 'excused'}, format='json')
        self.assertEqual(ok.status_code, 200)
        bad = self.client.patch(f'/api/v1/attendance/{self.record.pk}/', {'status': 'vacation'}, format='json')
        self.assertEqual(bad.status_code, 400)
        self.record.refresh_from_db()
        self.assertEqual(self.record.status, 'excused')

    # F1G-4
    def test_admin_bulk_records_unrecorded_students_atomically(self):
        self.auth(self.admin_user, self.admin_m)
        response = self.bulk()
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(response.json()['created'], 1)
        self.assertTrue(Attendance.objects.filter(student_enrollment=self.enrollment_two, status='late').exists())

    def test_admin_bulk_rejects_foreign_assignment_and_foreign_enrollment(self):
        self.auth(self.admin_user, self.admin_m)
        self.assertEqual(self.bulk(assignment_id=self.other_assignment.pk).status_code, 400)
        mixed = self.bulk(students=[
            {'student_enrollment_id': self.enrollment_two.pk, 'status': 'present'},
            {'student_enrollment_id': self.other_enrollment.pk, 'status': 'present'},
        ])
        self.assertEqual(mixed.status_code, 400)
        self.assertFalse(Attendance.objects.filter(student_enrollment=self.enrollment_two).exists())

    # F1G-5 + S3
    def test_historical_admin_can_read_but_never_write(self):
        self.make_historical()
        self.auth(self.admin_user, self.admin_m)
        self.assertEqual(self.client.get('/api/v1/attendance/').status_code, 200)
        self.assertEqual(self.client.get('/api/v1/attendance/daily/', {'date': DAY.isoformat()}).status_code, 200)
        self.assertEqual(
            self.client.patch(f'/api/v1/attendance/{self.record.pk}/', {'status': 'absent'}, format='json').status_code, 403,
        )
        self.assertEqual(self.bulk().status_code, 403)
        self.record.refresh_from_db()
        self.assertEqual(self.record.status, 'present')
        self.assertFalse(Attendance.objects.filter(student_enrollment=self.enrollment_two).exists())

    # S2
    def test_parent_and_student_cannot_write_or_read_daily_report(self):
        for user, membership in ((self.parent_user, self.parent_m), (self.student_user, self.student_m)):
            with self.subTest(role=membership.role):
                self.auth(user, membership)
                self.assertEqual(
                    self.client.patch(f'/api/v1/attendance/{self.record.pk}/', {'status': 'absent'}, format='json').status_code,
                    403,
                )
                self.assertEqual(self.bulk().status_code, 403)
                self.assertEqual(self.client.get('/api/v1/attendance/daily/').status_code, 403)

    def test_teacher_cannot_bulk_record_for_foreign_assignment(self):
        self.auth(self.teacher_user, self.teacher_m)
        self.assertEqual(self.bulk(assignment_id=self.other_assignment.pk).status_code, 400)

    def test_super_admin_scope_is_documented_global(self):
        """Documented behaviour: the shared attendance selector gives Super Admin
        every school's records, matching the AGENTS.md rule that super_admin
        sees all schools. Changing this needs an explicit architecture decision."""
        membership = SchoolMembership.objects.create(
            user=self.super_user, school=self.school, role='super_admin', status='active', is_default=True,
        )
        self.auth(self.super_user, membership)
        response = self.client.get('/api/v1/attendance/', {'attendance_date': DAY.isoformat()})
        self.assertEqual(response.status_code, 200)
        self.assertSetEqual({row['id'] for row in response.json()['results']}, {self.record.pk, self.foreign.pk})
