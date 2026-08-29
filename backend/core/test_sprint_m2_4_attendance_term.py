from datetime import date, timedelta
from decimal import Decimal

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from core.models import (
    AcademicTerm,
    AcademicYear,
    Attendance,
    Classroom,
    School,
    SchoolMembership,
    Section,
    Student,
    StudentEnrollment,
    Subject,
    Teacher,
    TeacherAssignment,
    User,
)


class SprintM24AttendanceTermResolutionTestCase(APITestCase):
    password = 'Teacher-test-pass-123!'
    today = date(2026, 3, 15)

    @classmethod
    def setUpTestData(cls):
        # 1. Schools
        cls.school_a = School.objects.create(name='Al-Noor Academy', code='SCH_NOOR')
        cls.school_b = School.objects.create(name='Al-Mustaqbal', code='SCH_FUTR')

        # 2. Academic Years
        cls.year_a_curr = AcademicYear.objects.create(
            school=cls.school_a,
            name='2025/2026',
            start_date=date(2025, 9, 1),
            end_date=date(2026, 8, 31),
            is_active=True,
        )
        cls.year_a_hist = AcademicYear.objects.create(
            school=cls.school_a,
            name='2024/2025',
            start_date=date(2024, 9, 1),
            end_date=date(2025, 8, 31),
            is_active=False,
        )
        cls.year_b_curr = AcademicYear.objects.create(
            school=cls.school_b,
            name='2025/2026',
            start_date=date(2025, 9, 1),
            end_date=date(2026, 8, 31),
            is_active=True,
        )

        # 3. Academic Terms for School A (Non-overlapping with mid-year break)
        cls.term_1 = AcademicTerm.objects.create(
            school=cls.school_a,
            academic_year=cls.year_a_curr,
            name='الفصل الدراسي الأول',
            term_type='term_1',
            start_date=date(2025, 9, 1),
            end_date=date(2026, 1, 15),
            is_active=True,
        )
        cls.term_2 = AcademicTerm.objects.create(
            school=cls.school_a,
            academic_year=cls.year_a_curr,
            name='الفصل الدراسي الثاني',
            term_type='term_2',
            start_date=date(2026, 2, 1),
            end_date=date(2026, 6, 30),
            is_active=True,
        )

        # Academic Term for School B
        cls.term_b = AcademicTerm.objects.create(
            school=cls.school_b,
            academic_year=cls.year_b_curr,
            name='Term B 1',
            term_type='term_1',
            start_date=date(2025, 9, 1),
            end_date=date(2026, 8, 31),
            is_active=True,
        )

        # Historical Term
        cls.term_hist = AcademicTerm.objects.create(
            school=cls.school_a,
            academic_year=cls.year_a_hist,
            name='Historical Term',
            term_type='term_1',
            start_date=date(2024, 9, 1),
            end_date=date(2025, 1, 31),
            is_active=False,
        )

        # 4. Subjects
        cls.sub_math = Subject.objects.create(school=cls.school_a, name='Mathematics', code='MATH')
        cls.sub_sci = Subject.objects.create(school=cls.school_a, name='Science', code='SCI')

        # 5. Classrooms & Sections
        cls.class_g6 = Classroom.objects.create(
            school=cls.school_a, academic_year=cls.year_a_curr, name='Grade 6', code='G6',
        )
        cls.sec_g6_a = Section.objects.create(
            school=cls.school_a, academic_year=cls.year_a_curr, classroom=cls.class_g6, name='Section A', code='A',
        )
        cls.sec_g6_b = Section.objects.create(
            school=cls.school_a, academic_year=cls.year_a_curr, classroom=cls.class_g6, name='Section B', code='B',
        )

        # 6. Users & Memberships
        cls.teacher_user = User.objects.create_user(
            username='teacher_ahmed_m24', email='ahmed_m24@noor.edu', role='teacher',
            school=cls.school_a, academic_year=cls.year_a_curr, is_active_school_user=True,
        )
        cls.teacher_user.set_password(cls.password)
        cls.teacher_user.save()

        cls.teacher_profile = Teacher.objects.create(
            user=cls.teacher_user, school=cls.school_a, academic_year=cls.year_a_curr, employee_code='T001',
            full_name='Ahmed Al-Ghamdi', specialization='Mathematics', is_active=True,
        )

        cls.teacher_mem_curr = SchoolMembership.objects.create(
            user=cls.teacher_user, school=cls.school_a, role='teacher',
            status='active', is_default=True,
        )

        cls.teacher_hist_user = User.objects.create_user(
            username='teacher_hist_m24', email='hist_m24@noor.edu', role='teacher',
            school=cls.school_a, academic_year=cls.year_a_hist, is_active_school_user=True,
        )
        cls.teacher_hist_user.set_password(cls.password)
        cls.teacher_hist_user.save()

        cls.teacher_mem_hist = SchoolMembership.objects.create(
            user=cls.teacher_hist_user, school=cls.school_a, role='teacher',
            status='historical', is_default=False,
        )

        # 7. Teacher Assignment
        cls.assign_math_g6a = TeacherAssignment.objects.create(
            school=cls.school_a, academic_year=cls.year_a_curr, teacher=cls.teacher_profile,
            classroom=cls.class_g6, section=cls.sec_g6_a, subject=cls.sub_math,
            is_current=True, start_date=date(2025, 9, 1), end_date=date(2026, 6, 30),
        )

        # Assignment with constrained dates
        cls.assign_bounded = TeacherAssignment.objects.create(
            school=cls.school_a, academic_year=cls.year_a_curr, teacher=cls.teacher_profile,
            classroom=cls.class_g6, section=cls.sec_g6_a, subject=cls.sub_sci,
            is_current=True, start_date=date(2026, 3, 1), end_date=date(2026, 3, 31),
        )

        # 8. Students & Enrollments
        cls.student_1 = Student.objects.create(
            school=cls.school_a, student_code='STU001', full_name='Tariq Al-Harbi',
        )
        cls.enroll_1_g6a = StudentEnrollment.objects.create(
            student=cls.student_1, school=cls.school_a, academic_year=cls.year_a_curr,
            classroom=cls.class_g6, section=cls.sec_g6_a, status='active', is_current=True,
        )

        cls.student_2 = Student.objects.create(
            school=cls.school_a, student_code='STU002', full_name='Zaid Al-Otaibi',
        )
        cls.enroll_2_g6a = StudentEnrollment.objects.create(
            student=cls.student_2, school=cls.school_a, academic_year=cls.year_a_curr,
            classroom=cls.class_g6, section=cls.sec_g6_a, status='active', is_current=True,
        )

        cls.student_3 = Student.objects.create(
            school=cls.school_a, student_code='STU003', full_name='Faris Al-Ghamdi',
        )
        cls.enroll_3_g6b = StudentEnrollment.objects.create(
            student=cls.student_3, school=cls.school_a, academic_year=cls.year_a_curr,
            classroom=cls.class_g6, section=cls.sec_g6_b, status='active', is_current=True,
        )

    def auth_headers(self, membership):
        from rest_framework_simplejwt.tokens import RefreshToken
        token = RefreshToken.for_user(membership.user).access_token
        self.client.credentials(
            HTTP_AUTHORIZATION=f'Bearer {token}',
            HTTP_X_SCHOOL_MEMBERSHIP_ID=str(membership.pk),
        )
        return {}

    # 1. First-time bulk attendance WITHOUT academic_term_id succeeds
    def test_first_time_bulk_attendance_without_academic_term_id_succeeds(self):
        headers = self.auth_headers(self.teacher_mem_curr)
        # attendance_date = 2026-03-15 (falls in term_2: 2026-02-01 to 2026-06-30)
        payload = {
            'teacher_assignment_id': self.assign_math_g6a.id,
            'attendance_date': self.today.isoformat(),
            'students': [
                {'student_enrollment_id': self.enroll_1_g6a.id, 'status': 'present', 'note': 'On time'},
                {'student_enrollment_id': self.enroll_2_g6a.id, 'status': 'late', 'note': '10 min late'},
            ],
        }
        response = self.client.post('/api/v1/attendance/bulk/', payload, format='json', **headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['created'], 2)
        self.assertEqual(response.data['total'], 2)
        self.assertEqual(response.data['academic_term']['id'], self.term_2.id)
        self.assertEqual(response.data['academic_term']['name'], self.term_2.name)

        # Verify DB records
        att_1 = Attendance.objects.get(student_enrollment=self.enroll_1_g6a, attendance_date=self.today)
        self.assertEqual(att_1.academic_term, self.term_2)
        self.assertEqual(att_1.status, 'present')

        att_2 = Attendance.objects.get(student_enrollment=self.enroll_2_g6a, attendance_date=self.today)
        self.assertEqual(att_2.academic_term, self.term_2)
        self.assertEqual(att_2.status, 'late')

    # 2. Exactly one matching term: correct term is resolved and stored across different dates
    def test_exactly_one_matching_term_resolved_and_stored(self):
        headers = self.auth_headers(self.teacher_mem_curr)
        # Date in Term 1 (2025-10-15)
        term_1_date = date(2025, 10, 15)
        payload_1 = {
            'teacher_assignment_id': self.assign_math_g6a.id,
            'attendance_date': term_1_date.isoformat(),
            'students': [
                {'student_enrollment_id': self.enroll_1_g6a.id, 'status': 'present'},
            ],
        }
        res_1 = self.client.post('/api/v1/attendance/bulk/', payload_1, format='json', **headers)
        self.assertEqual(res_1.status_code, status.HTTP_200_OK)
        self.assertEqual(res_1.data['academic_term']['id'], self.term_1.id)

        att_1 = Attendance.objects.get(student_enrollment=self.enroll_1_g6a, attendance_date=term_1_date)
        self.assertEqual(att_1.academic_term, self.term_1)

    # 3. Zero matching terms: HTTP 400
    def test_zero_matching_terms_rejected_with_400(self):
        headers = self.auth_headers(self.teacher_mem_curr)
        # 2026-01-20 is inside teacher assignment (Sep 2025 - Jun 2026) but between term_1 and term_2
        mid_year_break_date = date(2026, 1, 20)
        payload = {
            'teacher_assignment_id': self.assign_math_g6a.id,
            'attendance_date': mid_year_break_date.isoformat(),
            'students': [
                {'student_enrollment_id': self.enroll_1_g6a.id, 'status': 'present'},
            ],
        }
        response = self.client.post('/api/v1/attendance/bulk/', payload, format='json', **headers)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('No academic term covers', str(response.data))

    # 4. Multiple matching terms: HTTP 400, no arbitrary term selected
    def test_multiple_matching_terms_rejected_with_400(self):
        # Create an overlapping term for the same date range
        overlapping_term = AcademicTerm.objects.create(
            school=self.school_a,
            academic_year=self.year_a_curr,
            name='Overlapping Term 3',
            term_type='term_3',
            start_date=date(2026, 3, 1),
            end_date=date(2026, 3, 31),
            is_active=True,
        )

        headers = self.auth_headers(self.teacher_mem_curr)
        payload = {
            'teacher_assignment_id': self.assign_math_g6a.id,
            'attendance_date': self.today.isoformat(),  # 2026-03-15 matches both term_2 and overlapping_term
            'students': [
                {'student_enrollment_id': self.enroll_1_g6a.id, 'status': 'present'},
            ],
        }
        response = self.client.post('/api/v1/attendance/bulk/', payload, format='json', **headers)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('ambiguous', str(response.data).lower())

        # Cleanup overlapping term
        overlapping_term.delete()

    # 5. Correct optional academic_term_id: succeeds (backward compatibility)
    def test_correct_optional_academic_term_id_succeeds(self):
        headers = self.auth_headers(self.teacher_mem_curr)
        payload = {
            'teacher_assignment_id': self.assign_math_g6a.id,
            'academic_term_id': self.term_2.id,
            'attendance_date': self.today.isoformat(),
            'students': [
                {'student_enrollment_id': self.enroll_1_g6a.id, 'status': 'present'},
            ],
        }
        response = self.client.post('/api/v1/attendance/bulk/', payload, format='json', **headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['academic_term']['id'], self.term_2.id)

    # 6. Wrong/mismatched academic_term_id: HTTP 400
    def test_wrong_or_mismatched_academic_term_id_rejected_with_400(self):
        headers = self.auth_headers(self.teacher_mem_curr)
        # Attendance date is in Term 2, but client passes Term 1 ID
        payload = {
            'teacher_assignment_id': self.assign_math_g6a.id,
            'academic_term_id': self.term_1.id,
            'attendance_date': self.today.isoformat(),
            'students': [
                {'student_enrollment_id': self.enroll_1_g6a.id, 'status': 'present'},
            ],
        }
        response = self.client.post('/api/v1/attendance/bulk/', payload, format='json', **headers)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('does not match', str(response.data))

    # 7. Term from another school or year: rejected with HTTP 400
    def test_term_from_another_school_or_year_rejected_with_400(self):
        headers = self.auth_headers(self.teacher_mem_curr)

        # From School B
        payload_b = {
            'teacher_assignment_id': self.assign_math_g6a.id,
            'academic_term_id': self.term_b.id,
            'attendance_date': self.today.isoformat(),
            'students': [
                {'student_enrollment_id': self.enroll_1_g6a.id, 'status': 'present'},
            ],
        }
        response_b = self.client.post('/api/v1/attendance/bulk/', payload_b, format='json', **headers)
        self.assertEqual(response_b.status_code, status.HTTP_400_BAD_REQUEST)

        # From historical year
        payload_hist = {
            'teacher_assignment_id': self.assign_math_g6a.id,
            'academic_term_id': self.term_hist.id,
            'attendance_date': self.today.isoformat(),
            'students': [
                {'student_enrollment_id': self.enroll_1_g6a.id, 'status': 'present'},
            ],
        }
        response_hist = self.client.post('/api/v1/attendance/bulk/', payload_hist, format='json', **headers)
        self.assertEqual(response_hist.status_code, status.HTTP_400_BAD_REQUEST)

    # 8. Historical Active Context: still HTTP 403 for write
    def test_historical_active_context_returns_403_forbidden(self):
        headers = self.auth_headers(self.teacher_mem_hist)
        payload = {
            'teacher_assignment_id': self.assign_math_g6a.id,
            'attendance_date': date(2024, 10, 15).isoformat(),
            'students': [
                {'student_enrollment_id': self.enroll_1_g6a.id, 'status': 'present'},
            ],
        }
        response = self.client.post('/api/v1/attendance/bulk/', payload, format='json', **headers)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # 9. Student outside TeacherAssignment scope: still rejected
    def test_student_outside_teacher_assignment_scope_rejected(self):
        headers = self.auth_headers(self.teacher_mem_curr)
        # enroll_3_g6b is in Section B, but assignment is for Section A
        payload = {
            'teacher_assignment_id': self.assign_math_g6a.id,
            'attendance_date': self.today.isoformat(),
            'students': [
                {'student_enrollment_id': self.enroll_1_g6a.id, 'status': 'present'},
                {'student_enrollment_id': self.enroll_3_g6b.id, 'status': 'present'},
            ],
        }
        response = self.client.post('/api/v1/attendance/bulk/', payload, format='json', **headers)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # 10. Existing attendance: bulk save updates/upserts rather than creating duplicate rows
    def test_existing_attendance_upserts_without_duplicates(self):
        headers = self.auth_headers(self.teacher_mem_curr)
        # Initial creation
        payload = {
            'teacher_assignment_id': self.assign_math_g6a.id,
            'attendance_date': self.today.isoformat(),
            'students': [
                {'student_enrollment_id': self.enroll_1_g6a.id, 'status': 'present', 'note': 'Present initially'},
                {'student_enrollment_id': self.enroll_2_g6a.id, 'status': 'absent', 'note': 'Unexcused'},
            ],
        }
        res_create = self.client.post('/api/v1/attendance/bulk/', payload, format='json', **headers)
        self.assertEqual(res_create.status_code, status.HTTP_200_OK)
        self.assertEqual(res_create.data['created'], 2)
        self.assertEqual(res_create.data['updated'], 0)

        # Correction / Update on the same date
        payload_update = {
            'teacher_assignment_id': self.assign_math_g6a.id,
            'attendance_date': self.today.isoformat(),
            'students': [
                {'student_enrollment_id': self.enroll_1_g6a.id, 'status': 'present', 'note': 'Updated note'},
                {'student_enrollment_id': self.enroll_2_g6a.id, 'status': 'excused', 'note': 'Doctor note provided'},
            ],
        }
        res_update = self.client.post('/api/v1/attendance/bulk/', payload_update, format='json', **headers)
        self.assertEqual(res_update.status_code, status.HTTP_200_OK)
        self.assertEqual(res_update.data['created'], 0)
        self.assertEqual(res_update.data['updated'], 2)

        # Total records for student 2 on today must remain exactly 1
        records_count = Attendance.objects.filter(
            student_enrollment=self.enroll_2_g6a, attendance_date=self.today,
        ).count()
        self.assertEqual(records_count, 1)

        att_2 = Attendance.objects.get(student_enrollment=self.enroll_2_g6a, attendance_date=self.today)
        self.assertEqual(att_2.status, 'excused')
        self.assertEqual(att_2.note, 'Doctor note provided')

    # 11. Duplicate student_enrollment_id inside one payload: still rejected
    def test_duplicate_student_enrollment_id_inside_payload_rejected(self):
        headers = self.auth_headers(self.teacher_mem_curr)
        payload = {
            'teacher_assignment_id': self.assign_math_g6a.id,
            'attendance_date': self.today.isoformat(),
            'students': [
                {'student_enrollment_id': self.enroll_1_g6a.id, 'status': 'present'},
                {'student_enrollment_id': self.enroll_1_g6a.id, 'status': 'late'},
            ],
        }
        response = self.client.post('/api/v1/attendance/bulk/', payload, format='json', **headers)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Duplicate student enrollment IDs', str(response.data))

    # 12. Invalid attendance status: still rejected
    def test_invalid_attendance_status_rejected(self):
        headers = self.auth_headers(self.teacher_mem_curr)
        payload = {
            'teacher_assignment_id': self.assign_math_g6a.id,
            'attendance_date': self.today.isoformat(),
            'students': [
                {'student_enrollment_id': self.enroll_1_g6a.id, 'status': 'invalid_status'},
            ],
        }
        response = self.client.post('/api/v1/attendance/bulk/', payload, format='json', **headers)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # 13. Attendance date outside assignment range: still rejected
    def test_attendance_date_outside_assignment_range_rejected(self):
        headers = self.auth_headers(self.teacher_mem_curr)
        # assign_bounded is valid from 2026-03-01 to 2026-03-31
        # 2026-02-15 is within term_2 (Feb-Jun) but outside assign_bounded (March only)
        out_of_bound_date = date(2026, 2, 15)
        payload = {
            'teacher_assignment_id': self.assign_bounded.id,
            'attendance_date': out_of_bound_date.isoformat(),
            'students': [
                {'student_enrollment_id': self.enroll_1_g6a.id, 'status': 'present'},
            ],
        }
        response = self.client.post('/api/v1/attendance/bulk/', payload, format='json', **headers)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # 14. Failed bulk request remains atomic
    def test_failed_bulk_request_remains_atomic(self):
        headers = self.auth_headers(self.teacher_mem_curr)
        date_atomic = date(2026, 3, 20)
        # Student 1 is valid, but Student 3 is in section B (invalid for this assignment)
        payload = {
            'teacher_assignment_id': self.assign_math_g6a.id,
            'attendance_date': date_atomic.isoformat(),
            'students': [
                {'student_enrollment_id': self.enroll_1_g6a.id, 'status': 'present'},
                {'student_enrollment_id': self.enroll_3_g6b.id, 'status': 'present'},
            ],
        }
        response = self.client.post('/api/v1/attendance/bulk/', payload, format='json', **headers)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Ensure NO attendance record was created for student 1 either
        exists = Attendance.objects.filter(
            student_enrollment=self.enroll_1_g6a, attendance_date=date_atomic,
        ).exists()
        self.assertFalse(exists)
