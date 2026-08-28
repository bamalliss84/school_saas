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
    Exam,
    ExamResult,
    ExamType,
    Homework,
    HomeworkSubmission,
    Parent,
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


class SprintM2TeacherBackendHardeningTestCase(APITestCase):
    password = 'Teacher-test-pass-123!'
    today = date(2026, 8, 28)

    @classmethod
    def setUpTestData(cls):
        # 1. Schools
        cls.school_a = School.objects.create(name='Al-Noor Academy', code='SCH_NOOR')
        cls.school_b = School.objects.create(name='Al-Mustaqbal', code='SCH_FUTR')

        # 2. Academic Years
        cls.year_a_curr = AcademicYear.objects.create(
            school=cls.school_a, name='2025/2026', start_date=date(2025, 9, 1), end_date=date(2026, 8, 31), is_active=True,
        )
        cls.year_a_hist = AcademicYear.objects.create(
            school=cls.school_a, name='2024/2025', start_date=date(2024, 9, 1), end_date=date(2025, 8, 31), is_active=False,
        )
        cls.year_b_curr = AcademicYear.objects.create(
            school=cls.school_b, name='2025/2026', start_date=date(2025, 9, 1), end_date=date(2026, 8, 31), is_active=True,
        )

        # 3. Academic Terms
        cls.term_a = AcademicTerm.objects.create(
            school=cls.school_a, academic_year=cls.year_a_curr, name='Term 1', term_type='term_1',
            start_date=date(2025, 9, 1), end_date=date(2026, 8, 31), is_active=True,
        )
        cls.term_b = AcademicTerm.objects.create(
            school=cls.school_b, academic_year=cls.year_b_curr, name='Term 1', term_type='term_1',
            start_date=date(2025, 9, 1), end_date=date(2026, 8, 31), is_active=True,
        )

        # 4. Subjects (School-Wide)
        cls.sub_math_a = Subject.objects.create(school=cls.school_a, name='Mathematics', code='MATH')
        cls.sub_sci_a = Subject.objects.create(school=cls.school_a, name='Science', code='SCI')
        cls.sub_math_b = Subject.objects.create(school=cls.school_b, name='Mathematics', code='MATH')

        # 5. Classrooms & Sections - School A Current Year
        cls.class_g6 = Classroom.objects.create(
            school=cls.school_a, academic_year=cls.year_a_curr, name='Grade 6', code='G6',
        )
        cls.sec_g6_a = Section.objects.create(
            school=cls.school_a, academic_year=cls.year_a_curr, classroom=cls.class_g6, name='Section A', code='A',
        )
        cls.sec_g6_b = Section.objects.create(
            school=cls.school_a, academic_year=cls.year_a_curr, classroom=cls.class_g6, name='Section B', code='B',
        )

        # School A Historical Year Class
        cls.class_g6_hist = Classroom.objects.create(
            school=cls.school_a, academic_year=cls.year_a_hist, name='Grade 6 Hist', code='G6H',
        )
        cls.sec_g6_hist = Section.objects.create(
            school=cls.school_a, academic_year=cls.year_a_hist, classroom=cls.class_g6_hist, name='Section A Hist', code='AH',
        )

        # School B Class
        cls.class_g6_b = Classroom.objects.create(
            school=cls.school_b, academic_year=cls.year_b_curr, name='Grade 6 B', code='G6B',
        )
        cls.sec_g6_b_a = Section.objects.create(
            school=cls.school_b, academic_year=cls.year_b_curr, classroom=cls.class_g6_b, name='Section A', code='BA',
        )

        # 6. Users & Memberships
        cls.teacher_user = User.objects.create_user(
            username='teacher_ahmed', email='ahmed@noor.edu', role='teacher',
            school=cls.school_a, academic_year=cls.year_a_curr, is_active_school_user=True,
        )
        cls.teacher_user.set_password(cls.password)
        cls.teacher_user.save()

        cls.teacher_mem_curr = SchoolMembership.objects.create(
            user=cls.teacher_user, school=cls.school_a, role='teacher', status='active', is_default=True,
        )
        cls.teacher_mem_b = SchoolMembership.objects.create(
            user=cls.teacher_user, school=cls.school_b, role='teacher', status='active', is_default=False,
        )

        cls.teacher_hist_user = User.objects.create_user(
            username='teacher_hist', email='hist@noor.edu', role='teacher',
            school=cls.school_a, academic_year=cls.year_a_hist, is_active_school_user=True,
        )
        cls.teacher_hist_user.set_password(cls.password)
        cls.teacher_hist_user.save()
        cls.teacher_mem_hist = SchoolMembership.objects.create(
            user=cls.teacher_hist_user, school=cls.school_a, role='teacher', status='historical', is_default=False,
        )

        cls.teacher_other_user = User.objects.create_user(
            username='teacher_sara', email='sara@noor.edu', role='teacher',
            school=cls.school_a, academic_year=cls.year_a_curr, is_active_school_user=True,
        )
        cls.teacher_other_user.set_password(cls.password)
        cls.teacher_other_user.save()
        cls.teacher_other_mem = SchoolMembership.objects.create(
            user=cls.teacher_other_user, school=cls.school_a, role='teacher', status='active', is_default=True,
        )

        cls.student_user = User.objects.create_user(
            username='student_ali', email='ali@noor.edu', role='student',
            school=cls.school_a, academic_year=cls.year_a_curr, is_active_school_user=True,
        )
        cls.student_mem = SchoolMembership.objects.create(
            user=cls.student_user, school=cls.school_a, role='student', status='active', is_default=True,
        )

        cls.admin_user = User.objects.create_user(
            username='admin_noor', email='admin@noor.edu', role='school_admin',
            school=cls.school_a, academic_year=cls.year_a_curr, is_active_school_user=True,
        )
        cls.admin_mem = SchoolMembership.objects.create(
            user=cls.admin_user, school=cls.school_a, role='school_admin', status='active', is_default=True,
        )

        # 7. Teacher Profiles
        cls.teacher_ahmed = Teacher.objects.create(
            school=cls.school_a, academic_year=cls.year_a_curr, user=cls.teacher_user,
            full_name='Ahmed Al-Mansoor', employee_code='SCH_NOOR-T00001',
            specialization='Mathematics', qualification='B.Sc. Mathematics', is_active=True,
        )
        cls.teacher_sara = Teacher.objects.create(
            school=cls.school_a, academic_year=cls.year_a_curr, user=cls.teacher_other_user,
            full_name='Sara Al-Ghamdi', employee_code='SCH_NOOR-T00002',
            specialization='Science', qualification='M.Sc. Physics', is_active=True,
        )

        # 8. Teacher Assignments
        # Ahmed: School A, Curr Year, G6-A, Math
        cls.assign_ahmed_g6a_math = TeacherAssignment.objects.create(
            teacher=cls.teacher_ahmed, school=cls.school_a, academic_year=cls.year_a_curr,
            classroom=cls.class_g6, section=cls.sec_g6_a, subject=cls.sub_math_a, is_current=True,
        )
        # Sara: School A, Curr Year, G6-B, Science
        cls.assign_sara_g6b_sci = TeacherAssignment.objects.create(
            teacher=cls.teacher_sara, school=cls.school_a, academic_year=cls.year_a_curr,
            classroom=cls.class_g6, section=cls.sec_g6_b, subject=cls.sub_sci_a, is_current=True,
        )
        # Ahmed: School A, Historical Year, G6-Hist, Math
        cls.assign_ahmed_hist = TeacherAssignment.objects.create(
            teacher=cls.teacher_ahmed, school=cls.school_a, academic_year=cls.year_a_hist,
            classroom=cls.class_g6_hist, section=cls.sec_g6_hist, subject=cls.sub_math_a, is_current=False,
        )


        # 9. Students & Enrollments
        cls.student_1 = Student.objects.create(
            school=cls.school_a, user=cls.student_user, full_name='Ali Ahmed', gender='male',
        )
        cls.enroll_1_g6a = StudentEnrollment.objects.create(
            student=cls.student_1, school=cls.school_a, academic_year=cls.year_a_curr,
            classroom=cls.class_g6, section=cls.sec_g6_a, status='active', is_current=True,
        )

        cls.student_2 = Student.objects.create(
            school=cls.school_a, full_name='Omar Khalid', gender='male',
        )
        cls.enroll_2_g6a = StudentEnrollment.objects.create(
            student=cls.student_2, school=cls.school_a, academic_year=cls.year_a_curr,
            classroom=cls.class_g6, section=cls.sec_g6_a, status='active', is_current=True,
        )

        # Student in Section B (Sara's section, not Ahmed's)
        cls.student_3_sec_b = Student.objects.create(
            school=cls.school_a, full_name='Zaid Hassan', gender='male',
        )
        cls.enroll_3_g6b = StudentEnrollment.objects.create(
            student=cls.student_3_sec_b, school=cls.school_a, academic_year=cls.year_a_curr,
            classroom=cls.class_g6, section=cls.sec_g6_b, status='active', is_current=True,
        )

        # Student in School B
        cls.student_sch_b = Student.objects.create(
            school=cls.school_b, full_name='Badr School B', gender='male',
        )
        cls.enroll_sch_b = StudentEnrollment.objects.create(
            student=cls.student_sch_b, school=cls.school_b, academic_year=cls.year_b_curr,
            classroom=cls.class_g6_b, section=cls.sec_g6_b_a, status='active', is_current=True,
        )

        # 10. Exam Types & Exams
        cls.exam_type = ExamType.objects.create(
            school=cls.school_a, name='Midterm Exam', code='MID', max_score=Decimal('100.00'), weight_percentage=Decimal('30.00'),
        )
        cls.exam_g6a_math = Exam.objects.create(
            school=cls.school_a, academic_year=cls.year_a_curr, academic_term=cls.term_a,
            exam_type=cls.exam_type, teacher_assignment=cls.assign_ahmed_g6a_math,
            title='Midterm Math G6A', total_marks=Decimal('100.00'),
            exam_date=cls.today, created_by=cls.teacher_user,
        )

    def auth_headers(self, membership):
        from rest_framework_simplejwt.tokens import RefreshToken
        token = RefreshToken.for_user(membership.user).access_token
        self.client.credentials(
            HTTP_AUTHORIZATION=f'Bearer {token}',
            HTTP_X_SCHOOL_MEMBERSHIP_ID=str(membership.pk),
        )
        return {}


    # =========================================================================
    # A. Teacher Profile Contract
    # =========================================================================
    def test_teacher_me_profile_returns_active_context_details(self):
        headers = self.auth_headers(self.teacher_mem_curr)
        response = self.client.get('/api/v1/teachers/me/profile/', **headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data
        self.assertEqual(data['id'], self.teacher_ahmed.id)
        self.assertEqual(data['full_name'], 'Ahmed Al-Mansoor')
        self.assertEqual(data['employee_code'], 'SCH_NOOR-T00001')
        self.assertEqual(data['specialization'], 'Mathematics')
        self.assertEqual(data['school']['id'], self.school_a.id)
        self.assertEqual(data['academic_year']['id'], self.year_a_curr.id)
        self.assertEqual(data['role'], 'teacher')

    def test_teacher_me_profile_denies_non_teacher(self):
        headers = self.auth_headers(self.student_mem)
        response = self.client.get('/api/v1/teachers/me/profile/', **headers)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # =========================================================================
    # B. Teacher Assignments & Classes & Subjects Isolation
    # =========================================================================
    def test_teacher_assignments_returns_only_active_school_and_current_year(self):
        headers = self.auth_headers(self.teacher_mem_curr)
        response = self.client.get('/api/v1/teachers/me/assignments/?current=true', **headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = [item['id'] for item in response.data['results']]
        self.assertIn(self.assign_ahmed_g6a_math.id, ids)
        self.assertNotIn(self.assign_sara_g6b_sci.id, ids)
        self.assertNotIn(self.assign_ahmed_hist.id, ids)

    def test_teacher_classes_returns_assigned_classes_only(self):
        headers = self.auth_headers(self.teacher_mem_curr)
        response = self.client.get('/api/v1/teachers/me/classes/', **headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        sections = [item['section']['id'] for item in response.data['results']]
        self.assertIn(self.sec_g6_a.id, sections)
        self.assertNotIn(self.sec_g6_b.id, sections)

    def test_teacher_subjects_returns_school_wide_subjects(self):
        headers = self.auth_headers(self.teacher_mem_curr)
        response = self.client.get('/api/v1/teachers/me/subjects/', **headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        codes = [item['code'] for item in response.data['results']]
        self.assertIn('MATH', codes)
        self.assertNotIn('SCI', codes)

    # =========================================================================
    # C. Assignment-Specific Roster Contract
    # =========================================================================
    def test_assignment_roster_returns_students_and_attendance_state(self):
        # Create an attendance record for Ali Ahmed
        Attendance.objects.create(
            student_enrollment=self.enroll_1_g6a,
            teacher_assignment=self.assign_ahmed_g6a_math,
            academic_term=self.term_a,
            attendance_date=self.today,
            status='present',
            note='Punctual',
        )

        headers = self.auth_headers(self.teacher_mem_curr)
        url = f'/api/v1/teachers/me/assignments/{self.assign_ahmed_g6a_math.id}/students/?date={self.today.isoformat()}'
        response = self.client.get(url, **headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.data
        self.assertEqual(data['assignment_id'], self.assign_ahmed_g6a_math.id)
        self.assertEqual(data['total_students'], 2)  # Ali and Omar
        self.assertEqual(data['recorded_count'], 1)  # Ali has attendance recorded

        roster = data['roster']
        enrollment_ids = [item['student_enrollment_id'] for item in roster]
        self.assertIn(self.enroll_1_g6a.id, enrollment_ids)
        self.assertIn(self.enroll_2_g6a.id, enrollment_ids)
        self.assertNotIn(self.enroll_3_g6b.id, enrollment_ids)
        self.assertNotIn(self.enroll_sch_b.id, enrollment_ids)

        ali_item = next(item for item in roster if item['student_enrollment_id'] == self.enroll_1_g6a.id)
        self.assertIsNotNone(ali_item['attendance'])
        self.assertEqual(ali_item['attendance']['status'], 'present')
        self.assertEqual(ali_item['attendance']['note'], 'Punctual')

        omar_item = next(item for item in roster if item['student_enrollment_id'] == self.enroll_2_g6a.id)
        self.assertIsNone(omar_item['attendance'])

    def test_assignment_roster_denies_another_teachers_assignment(self):
        headers = self.auth_headers(self.teacher_mem_curr)
        url = f'/api/v1/teachers/me/assignments/{self.assign_sara_g6b_sci.id}/students/'
        response = self.client.get(url, **headers)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_assignment_roster_denies_foreign_school_assignment(self):
        assign_b = TeacherAssignment.objects.create(
            teacher=self.teacher_ahmed, school=self.school_b, academic_year=self.year_b_curr,
            classroom=self.class_g6_b, section=self.sec_g6_b_a, subject=self.sub_math_b, is_current=True,
        )
        headers = self.auth_headers(self.teacher_mem_curr)
        url = f'/api/v1/teachers/me/assignments/{assign_b.id}/students/'
        response = self.client.get(url, **headers)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # =========================================================================
    # D. Attendance Contract Hardening
    # =========================================================================
    def test_bulk_attendance_success_and_correction(self):
        headers = self.auth_headers(self.teacher_mem_curr)
        payload = {
            'teacher_assignment_id': self.assign_ahmed_g6a_math.id,
            'academic_term_id': self.term_a.id,
            'attendance_date': self.today.isoformat(),
            'students': [
                {'student_enrollment_id': self.enroll_1_g6a.id, 'status': 'present', 'note': 'Present'},
                {'student_enrollment_id': self.enroll_2_g6a.id, 'status': 'late', 'note': '5 mins late'},
            ],
        }
        # 1. Create bulk
        response = self.client.post('/api/v1/attendance/bulk/', payload, format='json', **headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['created'], 2)
        self.assertEqual(response.data['total'], 2)

        # 2. Correction / Update
        payload['students'][1]['status'] = 'excused'
        response2 = self.client.post('/api/v1/attendance/bulk/', payload, format='json', **headers)
        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        self.assertEqual(response2.data['updated'], 2)

        record = Attendance.objects.get(student_enrollment=self.enroll_2_g6a, attendance_date=self.today)
        self.assertEqual(record.status, 'excused')

    def test_bulk_attendance_rejects_unauthorized_assignment(self):
        headers = self.auth_headers(self.teacher_mem_curr)
        payload = {
            'teacher_assignment_id': self.assign_sara_g6b_sci.id,
            'academic_term_id': self.term_a.id,
            'attendance_date': self.today.isoformat(),
            'students': [
                {'student_enrollment_id': self.enroll_3_g6b.id, 'status': 'present'},
            ],
        }
        response = self.client.post('/api/v1/attendance/bulk/', payload, format='json', **headers)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_bulk_attendance_rejects_foreign_student_outside_section(self):
        headers = self.auth_headers(self.teacher_mem_curr)
        payload = {
            'teacher_assignment_id': self.assign_ahmed_g6a_math.id,
            'academic_term_id': self.term_a.id,
            'attendance_date': self.today.isoformat(),
            'students': [
                {'student_enrollment_id': self.enroll_1_g6a.id, 'status': 'present'},
                {'student_enrollment_id': self.enroll_3_g6b.id, 'status': 'present'},  # In section B!
            ],
        }
        response = self.client.post('/api/v1/attendance/bulk/', payload, format='json', **headers)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_attendance_mutation_rejected_in_historical_context(self):
        headers = self.auth_headers(self.teacher_mem_hist)
        payload = {
            'teacher_assignment_id': self.assign_ahmed_g6a_math.id,
            'academic_term_id': self.term_a.id,
            'attendance_date': self.today.isoformat(),
            'students': [
                {'student_enrollment_id': self.enroll_1_g6a.id, 'status': 'present'},
            ],
        }
        response = self.client.post('/api/v1/attendance/bulk/', payload, format='json', **headers)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # =========================================================================
    # E. Homework + Submissions Contract
    # =========================================================================
    def test_teacher_can_create_homework_for_assigned_class(self):
        headers = self.auth_headers(self.teacher_mem_curr)
        payload = {
            'teacher_assignment': self.assign_ahmed_g6a_math.id,
            'academic_term': self.term_a.id,
            'title': 'Chapter 1 Math Homework',
            'description': 'Solve exercises 1 to 10',
            'max_grade': '10.00',
            'due_date': (self.today + timedelta(days=3)).strftime('%Y-%m-%dT18:00:00Z'),
            'status': 'draft',
        }
        response = self.client.post('/api/v1/homework/', payload, format='json', **headers)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertEqual(response.data['title'], 'Chapter 1 Math Homework')

    def test_teacher_cannot_create_homework_for_unassigned_class(self):
        headers = self.auth_headers(self.teacher_mem_curr)
        payload = {
            'teacher_assignment': self.assign_sara_g6b_sci.id,
            'academic_term': self.term_a.id,
            'title': 'Science Homework',
            'description': 'Physics lab',
            'max_grade': '10.00',
            'due_date': (self.today + timedelta(days=3)).strftime('%Y-%m-%dT18:00:00Z'),
            'status': 'draft',
        }
        response = self.client.post('/api/v1/homework/', payload, format='json', **headers)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


    # =========================================================================
    # F. Exams & Results Workflow
    # =========================================================================
    def test_teacher_can_bulk_grade_and_submit_result(self):
        headers = self.auth_headers(self.teacher_mem_curr)
        payload = {
            'exam': self.exam_g6a_math.id,
            'results': [
                {'student_enrollment': self.enroll_1_g6a.id, 'status': 'present', 'score': '88.50', 'remarks': 'Great effort'},
                {'student_enrollment': self.enroll_2_g6a.id, 'status': 'present', 'score': '74.00', 'remarks': 'Good'},
            ],
        }
        response = self.client.post('/api/v1/exam-results/bulk/', payload, format='json', **headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        result_1 = ExamResult.objects.get(exam=self.exam_g6a_math, student_enrollment=self.enroll_1_g6a)
        self.assertEqual(result_1.workflow_status, 'draft')
        self.assertEqual(result_1.score, Decimal('88.50'))

        # Teacher submits result for approval
        sub_resp = self.client.post(f'/api/v1/exam-results/{result_1.id}/submit/', {}, format='json', **headers)
        self.assertEqual(sub_resp.status_code, status.HTTP_200_OK)
        result_1.refresh_from_db()
        self.assertEqual(result_1.workflow_status, 'submitted')

    def test_teacher_cannot_approve_or_publish_exam_results(self):
        result = ExamResult.objects.create(
            exam=self.exam_g6a_math, student_enrollment=self.enroll_1_g6a,
            status='present', score=Decimal('90.00'), workflow_status='submitted',
        )
        headers = self.auth_headers(self.teacher_mem_curr)

        # Try to approve
        approve_resp = self.client.post(f'/api/v1/exam-results/{result.id}/approve/', {}, format='json', **headers)
        self.assertEqual(approve_resp.status_code, status.HTTP_403_FORBIDDEN)

        # Try to publish
        pub_resp = self.client.post(f'/api/v1/exams/{self.exam_g6a_math.id}/publish/', {}, format='json', **headers)
        self.assertEqual(pub_resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_multi_school_teacher_context_switching(self):
        # Teacher Ahmed has assignments in School A and School B
        assign_b = TeacherAssignment.objects.create(
            teacher=self.teacher_ahmed, school=self.school_b, academic_year=self.year_b_curr,
            classroom=self.class_g6_b, section=self.sec_g6_b_a, subject=self.sub_math_b, is_current=True,
        )

        # Query in School A context
        headers_a = self.auth_headers(self.teacher_mem_curr)
        res_a = self.client.get('/api/v1/teachers/me/assignments/', **headers_a)
        self.assertEqual(res_a.status_code, status.HTTP_200_OK)
        ids_a = [item['id'] for item in res_a.data['results']]
        self.assertIn(self.assign_ahmed_g6a_math.id, ids_a)
        self.assertNotIn(assign_b.id, ids_a)

        # Query in School B context
        headers_b = self.auth_headers(self.teacher_mem_b)
        res_b = self.client.get('/api/v1/teachers/me/assignments/', **headers_b)
        self.assertEqual(res_b.status_code, status.HTTP_200_OK)
        ids_b = [item['id'] for item in res_b.data['results']]
        self.assertIn(assign_b.id, ids_b)
        self.assertNotIn(self.assign_ahmed_g6a_math.id, ids_b)

    def test_bulk_attendance_rejects_duplicate_students(self):
        headers = self.auth_headers(self.teacher_mem_curr)
        payload = {
            'teacher_assignment_id': self.assign_ahmed_g6a_math.id,
            'academic_term_id': self.term_a.id,
            'attendance_date': self.today.isoformat(),
            'students': [
                {'student_enrollment_id': self.enroll_1_g6a.id, 'status': 'present'},
                {'student_enrollment_id': self.enroll_1_g6a.id, 'status': 'late'},  # Duplicate!
            ],
        }
        response = self.client.post('/api/v1/attendance/bulk/', payload, format='json', **headers)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_teacher_grading_submission_security(self):
        # Create a published homework
        hw = Homework.objects.create(
            school=self.school_a, academic_year=self.year_a_curr, academic_term=self.term_a,
            teacher_assignment=self.assign_ahmed_g6a_math, title='HW 1',
            status='published', due_date=self.today + timedelta(days=2),
            published_at=self.today - timedelta(days=1), max_grade=Decimal('10.00'),
            submission_type='text', created_by=self.teacher_user,
        )
        submission = HomeworkSubmission.objects.create(
            homework=hw, student_enrollment=self.enroll_1_g6a,
            status='submitted', answer='Here is my answer',
            submitted_at=self.today,
        )

        # Teacher Ahmed (assigned) can grade
        headers_ahmed = self.auth_headers(self.teacher_mem_curr)
        grade_payload = {'grade': '9.50', 'teacher_note': 'Excellent work'}
        grade_resp = self.client.post(f'/api/v1/homework-submissions/{submission.id}/grade/', grade_payload, format='json', **headers_ahmed)
        self.assertEqual(grade_resp.status_code, status.HTTP_200_OK)
        submission.refresh_from_db()
        self.assertEqual(submission.status, 'graded')
        self.assertEqual(submission.grade, Decimal('9.50'))

        # Reset submission
        submission.status = 'submitted'
        submission.grade = None
        submission.save()

        # Teacher Sara (unassigned) cannot grade
        headers_sara = self.auth_headers(self.teacher_other_mem)
        sara_resp = self.client.post(f'/api/v1/homework-submissions/{submission.id}/grade/', grade_payload, format='json', **headers_sara)
        self.assertEqual(sara_resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_historical_context_mutation_rejected_across_domains(self):
        headers_hist = self.auth_headers(self.teacher_mem_hist)

        # Homework creation rejected
        hw_payload = {
            'teacher_assignment': self.assign_ahmed_g6a_math.id,
            'academic_term': self.term_a.id,
            'title': 'Hist HW',
            'max_grade': '10.00',
            'due_date': (self.today + timedelta(days=3)).strftime('%Y-%m-%dT18:00:00Z'),
            'status': 'draft',
        }
        res_hw = self.client.post('/api/v1/homework/', hw_payload, format='json', **headers_hist)
        self.assertEqual(res_hw.status_code, status.HTTP_403_FORBIDDEN)

        # Exam result grading rejected
        exam_payload = {
            'exam': self.exam_g6a_math.id,
            'results': [
                {'student_enrollment': self.enroll_1_g6a.id, 'status': 'present', 'score': '90.00'},
            ],
        }
        res_exam = self.client.post('/api/v1/exam-results/bulk/', exam_payload, format='json', **headers_hist)
        self.assertEqual(res_exam.status_code, status.HTTP_403_FORBIDDEN)

