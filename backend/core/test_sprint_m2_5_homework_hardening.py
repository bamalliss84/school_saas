from datetime import date, datetime, timedelta
from decimal import Decimal
import shutil
import tempfile

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from core.context import ensure_legacy_membership
from core.models import (
    AcademicTerm,
    AcademicYear,
    Classroom,
    Homework,
    HomeworkAttachment,
    HomeworkSubmission,
    HomeworkSubmissionAttachment,
    School,
    SchoolMembership,
    Section,
    Student,
    StudentEnrollment,
    StudentGuardian,
    Subject,
    Teacher,
    TeacherAssignment,
    User,
)
from core.services.homework import (
    create_submission_draft,
    final_submit_homework,
    grade_submission,
    publish_homework,
)


class SprintM25HomeworkHardeningTests(APITestCase):
    password = 'Hardening-test-pass-123!'

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

        # 3. Academic Terms for School A
        cls.term_1 = AcademicTerm.objects.create(
            school=cls.school_a,
            academic_year=cls.year_a_curr,
            name='Term 1 (Fall)',
            term_type='term_1',
            start_date=date(2025, 9, 1),
            end_date=date(2025, 12, 31),
            is_active=False,
        )
        cls.term_2 = AcademicTerm.objects.create(
            school=cls.school_a,
            academic_year=cls.year_a_curr,
            name='Term 2 (Spring)',
            term_type='term_2',
            start_date=date(2026, 2, 1),
            end_date=date(2026, 6, 30),
            is_active=True,
        )
        cls.term_hist = AcademicTerm.objects.create(
            school=cls.school_a,
            academic_year=cls.year_a_hist,
            name='Term 1 Hist',
            term_type='term_1',
            start_date=date(2024, 9, 1),
            end_date=date(2024, 12, 31),
            is_active=False,
        )

        # School B Term
        cls.term_b = AcademicTerm.objects.create(
            school=cls.school_b,
            academic_year=cls.year_b_curr,
            name='Term B (Spring)',
            term_type='term_2',
            start_date=date(2026, 2, 1),
            end_date=date(2026, 6, 30),
            is_active=True,
        )

        # 4. Classrooms, Sections, Subjects
        cls.class_10a = Classroom.objects.create(school=cls.school_a, academic_year=cls.year_a_curr, name='Grade 10', code='G10')
        cls.sec_1 = Section.objects.create(school=cls.school_a, classroom=cls.class_10a, academic_year=cls.year_a_curr, name='Section 1', code='SEC1')
        cls.sec_2 = Section.objects.create(school=cls.school_a, classroom=cls.class_10a, academic_year=cls.year_a_curr, name='Section 2', code='SEC2')
        cls.sub_math = Subject.objects.create(school=cls.school_a, name='Mathematics', code='MATH10')

        cls.class_b = Classroom.objects.create(school=cls.school_b, academic_year=cls.year_b_curr, name='Grade 11', code='G11')
        cls.sec_b = Section.objects.create(school=cls.school_b, classroom=cls.class_b, academic_year=cls.year_b_curr, name='Section B', code='SECB')
        cls.sub_sci_b = Subject.objects.create(school=cls.school_b, name='Physics', code='PHY11')

        # 5. Users
        # Teacher User in School A
        cls.teacher_user = User.objects.create_user(
            username='multi_teacher',
            email='teacher@saas.local',
            password=cls.password,
            first_name='Tariq',
            last_name='Al-Mansoor',
            role='teacher',
            school=cls.school_a,
            academic_year=cls.year_a_curr,
        )
        cls.teacher_a = Teacher.objects.create(
            school=cls.school_a,
            academic_year=cls.year_a_curr,
            user=cls.teacher_user,
            employee_code='T-1001',
            full_name='Tariq Al-Mansoor',
            is_active=True,
        )
        cls.mb_teacher_a = SchoolMembership.objects.create(
            user=cls.teacher_user, school=cls.school_a, role='teacher', status='active', is_default=True,
        )
        cls.mb_teacher_b = SchoolMembership.objects.create(
            user=cls.teacher_user, school=cls.school_b, role='teacher', status='active', is_default=False,
        )

        # Historical Teacher User in School A
        cls.teacher_hist_user = User.objects.create_user(
            username='teacher_hist',
            email='hist@saas.local',
            password=cls.password,
            first_name='Historical',
            last_name='Teacher',
            role='teacher',
            school=cls.school_a,
            academic_year=cls.year_a_hist,
        )
        cls.mb_teacher_hist = SchoolMembership.objects.create(
            user=cls.teacher_hist_user, school=cls.school_a, role='teacher', status='historical', is_default=False,
        )

        # Teacher User in School B
        cls.teacher_b_user = User.objects.create_user(
            username='teacher_b',
            email='teacher_b@saas.local',
            password=cls.password,
            first_name='Bassem',
            last_name='Teacher',
            role='teacher',
            school=cls.school_b,
            academic_year=cls.year_b_curr,
        )
        cls.teacher_b = Teacher.objects.create(
            school=cls.school_b,
            academic_year=cls.year_b_curr,
            user=cls.teacher_b_user,
            employee_code='T-2001',
            full_name='Bassem Teacher',
            is_active=True,
        )
        cls.mb_teacher_b_user = SchoolMembership.objects.create(
            user=cls.teacher_b_user, school=cls.school_b, role='teacher', status='active', is_default=True,
        )

        # Multi-role User: Admin in School A, Teacher in School B
        cls.multirole_user = User.objects.create_user(
            username='multirole_user',
            email='multirole@saas.local',
            password=cls.password,
            first_name='Mona',
            last_name='Admin',
            role='school_admin',
            school=cls.school_a,
            academic_year=cls.year_a_curr,
        )
        cls.mb_admin_a = SchoolMembership.objects.create(
            user=cls.multirole_user, school=cls.school_a, role='school_admin', status='active', is_default=True,
        )

        # 6. Teacher Assignments
        cls.assign_a = TeacherAssignment.objects.create(
            teacher=cls.teacher_a,
            school=cls.school_a,
            academic_year=cls.year_a_curr,
            classroom=cls.class_10a,
            section=cls.sec_1,
            subject=cls.sub_math,
            is_current=True,
        )
        cls.assign_b = TeacherAssignment.objects.create(
            teacher=cls.teacher_b,
            school=cls.school_b,
            academic_year=cls.year_b_curr,
            classroom=cls.class_b,
            section=cls.sec_b,
            subject=cls.sub_sci_b,
            is_current=True,
        )

        # 7. Students & Enrollments in School A Section 1
        cls.student_users = []
        cls.students = []
        cls.enrollments = []
        for i in range(4):
            stu_user = User.objects.create_user(
                username=f'student_{i+1}',
                email=f'stu{i+1}@saas.local',
                password=cls.password,
                first_name=f'Student{i+1}',
                last_name='Test',
                role='student',
                school=cls.school_a,
                academic_year=cls.year_a_curr,
            )
            stu = Student.objects.create(
                school=cls.school_a,
                user=stu_user,
                student_code=f'STU-100{i+1}',
                full_name=f'Student {i+1} Test',
                gender='male',
            )
            enr = StudentEnrollment.objects.create(
                student=stu,
                school=cls.school_a,
                academic_year=cls.year_a_curr,
                classroom=cls.class_10a,
                section=cls.sec_1,
                is_current=True,
                status='active',
            )
            SchoolMembership.objects.create(
                user=stu_user, school=cls.school_a, role='student', status='active', is_default=True,
            )
            cls.student_users.append(stu_user)
            cls.students.append(stu)
            cls.enrollments.append(enr)

        # Other section student (Section 2 - should not leak)
        cls.stu_sec2_user = User.objects.create_user(
            username='student_sec2',
            email='stusec2@saas.local',
            password=cls.password,
            first_name='StudentSec2',
            last_name='Test',
            role='student',
            school=cls.school_a,
            academic_year=cls.year_a_curr,
        )
        cls.stu_sec2 = Student.objects.create(
            school=cls.school_a,
            user=cls.stu_sec2_user,
            student_code='STU-SEC2',
            full_name='Student Sec2 Test',
            gender='female',
        )
        cls.enr_sec2 = StudentEnrollment.objects.create(
            student=cls.stu_sec2,
            school=cls.school_a,
            academic_year=cls.year_a_curr,
            classroom=cls.class_10a,
            section=cls.sec_2,
            is_current=True,
            status='active',
        )

    def setUp(self):
        self.media_root = tempfile.mkdtemp(prefix='saas-m25-tests-')
        self.settings_override = override_settings(MEDIA_ROOT=self.media_root)
        self.settings_override.enable()

    def tearDown(self):
        self.settings_override.disable()
        shutil.rmtree(self.media_root, ignore_errors=True)

    def auth_membership(self, user, membership):
        token = RefreshToken.for_user(user).access_token
        self.client.credentials(
            HTTP_AUTHORIZATION=f'Bearer {token}',
            HTTP_X_SCHOOL_MEMBERSHIP_ID=str(membership.pk),
        )

    # =========================================================================
    # 1. ACADEMIC TERM RESOLUTION
    # =========================================================================

    def test_01_omitted_academic_term_resolves_from_due_date(self):
        """When academic_term is omitted, server resolves term matching due_date."""
        self.auth_membership(self.teacher_user, self.mb_teacher_a)
        response = self.client.post('/api/v1/homework/', {
            'teacher_assignment': self.assign_a.pk,
            'title': 'Term 2 Homework',
            'due_date': '2026-03-15T18:00:00Z',
            'max_grade': '20.00',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['academic_term'], self.term_2.pk)

    def test_02_supplied_correct_academic_term_accepted(self):
        """When correct academic_term is supplied by client, it is accepted."""
        self.auth_membership(self.teacher_user, self.mb_teacher_a)
        response = self.client.post('/api/v1/homework/', {
            'teacher_assignment': self.assign_a.pk,
            'academic_term': self.term_2.pk,
            'title': 'Explicit Term 2',
            'due_date': '2026-04-10T18:00:00Z',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['academic_term'], self.term_2.pk)

    def test_03_supplied_wrong_academic_term_rejected(self):
        """When client supplies mismatched academic_term, HTTP 400 is returned."""
        self.auth_membership(self.teacher_user, self.mb_teacher_a)
        response = self.client.post('/api/v1/homework/', {
            'teacher_assignment': self.assign_a.pk,
            'academic_term': self.term_1.pk,  # Term 1 ended 2025-12-31; due date is 2026-03-15
            'title': 'Mismatch Term',
            'due_date': '2026-03-15T18:00:00Z',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        errors = response.data.get('errors', response.data)
        self.assertIn('academic_term', errors)

    def test_04_no_matching_academic_term_rejected(self):
        """When due_date falls in a break period with no term covering it, HTTP 400 is returned."""
        self.auth_membership(self.teacher_user, self.mb_teacher_a)
        # 2026-01-15 is during the mid-year break (Term 1 ended 2025-12-31, Term 2 starts 2026-02-01)
        response = self.client.post('/api/v1/homework/', {
            'teacher_assignment': self.assign_a.pk,
            'title': 'Break Homework',
            'due_date': '2026-01-15T18:00:00Z',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        errors = response.data.get('errors', response.data)
        self.assertIn('academic_term', errors)

    def test_05_ambiguous_matching_academic_terms_rejected(self):
        """When multiple overlapping terms cover the due date, HTTP 400 is returned."""
        overlap = AcademicTerm.objects.create(
            school=self.school_a,
            academic_year=self.year_a_curr,
            name='Summer Overlap',
            term_type='summer',
            start_date=date(2026, 3, 1),
            end_date=date(2026, 3, 31),
            is_active=True,
        )
        try:
            self.auth_membership(self.teacher_user, self.mb_teacher_a)
            response = self.client.post('/api/v1/homework/', {
                'teacher_assignment': self.assign_a.pk,
                'title': 'Ambiguous Term Homework',
                'due_date': '2026-03-15T18:00:00Z',
            }, format='json')
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            errors = response.data.get('errors', response.data)
            self.assertIn('academic_term', errors)
        finally:
            overlap.delete()

    # =========================================================================
    # 2. TEACHER CONTEXT & MULTI-SCHOOL ISOLATION
    # =========================================================================

    def test_06_multi_school_teacher_school_a_scope(self):
        """Teacher in School A context manages only School A homework."""
        self.auth_membership(self.teacher_user, self.mb_teacher_a)
        res_create = self.client.post('/api/v1/homework/', {
            'teacher_assignment': self.assign_a.pk,
            'title': 'School A Homework',
            'due_date': '2026-03-20T18:00:00Z',
        }, format='json')
        self.assertEqual(res_create.status_code, status.HTTP_201_CREATED)
        hw_a_id = res_create.data['id']

        # Attempt to create homework in School A context for School B assignment -> 400
        res_wrong = self.client.post('/api/v1/homework/', {
            'teacher_assignment': self.assign_b.pk,
            'title': 'Wrong School Assignment',
            'due_date': '2026-03-20T18:00:00Z',
        }, format='json')
        self.assertEqual(res_wrong.status_code, status.HTTP_400_BAD_REQUEST)

        # List homework in School A
        res_list = self.client.get('/api/v1/teachers/me/homework/')
        self.assertEqual(res_list.status_code, status.HTTP_200_OK)
        ids = [row['id'] for row in res_list.data['results']]
        self.assertIn(hw_a_id, ids)

    def test_07_switching_membership_to_school_b_switches_scope(self):
        """Switching to School B membership allows School B homework and hides School A."""
        # Create homework in School A by teacher A
        self.auth_membership(self.teacher_user, self.mb_teacher_a)
        res_a = self.client.post('/api/v1/homework/', {
            'teacher_assignment': self.assign_a.pk,
            'title': 'School A Only',
            'due_date': '2026-03-20T18:00:00Z',
        }, format='json')
        self.assertEqual(res_a.status_code, status.HTTP_201_CREATED)
        hw_a_id = res_a.data['id']

        # Create homework in School B by teacher B
        self.auth_membership(self.teacher_b_user, self.mb_teacher_b_user)
        res_b = self.client.post('/api/v1/homework/', {
            'teacher_assignment': self.assign_b.pk,
            'title': 'School B Only',
            'due_date': '2026-03-20T18:00:00Z',
        }, format='json')
        self.assertEqual(res_b.status_code, status.HTTP_201_CREATED)
        hw_b_id = res_b.data['id']

        # Direct retrieve School A homework while in School B context -> 404
        res_direct = self.client.get(f'/api/v1/homework/{hw_a_id}/')
        self.assertEqual(res_direct.status_code, status.HTTP_404_NOT_FOUND)

        # List in School B -> contains B, not A
        res_list = self.client.get('/api/v1/teachers/me/homework/')
        self.assertEqual(res_list.status_code, status.HTTP_200_OK)
        ids = [row['id'] for row in res_list.data['results']]
        self.assertIn(hw_b_id, ids)
        self.assertNotIn(hw_a_id, ids)

        # Teacher user switching to School B membership without School B assignment sees empty list
        self.auth_membership(self.teacher_user, self.mb_teacher_b)
        res_teacher_b_ctx = self.client.get('/api/v1/teachers/me/homework/')
        self.assertEqual(res_teacher_b_ctx.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res_teacher_b_ctx.data['results']), 0)

    def test_08_multi_role_user_uses_active_membership_role(self):
        """Multi-role user (Admin in School A, Teacher in School B) enforces active role."""
        # Active role: School Admin in School A -> can manage School A homework
        self.auth_membership(self.multirole_user, self.mb_admin_a)
        res_admin = self.client.post('/api/v1/homework/', {
            'teacher_assignment': self.assign_a.pk,
            'title': 'Admin Created HW',
            'due_date': '2026-03-20T18:00:00Z',
        }, format='json')
        self.assertEqual(res_admin.status_code, status.HTTP_201_CREATED)

    # =========================================================================
    # 3. HISTORICAL CONTEXT REJECTS ALL WRITES
    # =========================================================================

    def test_09_historical_context_rejects_all_mutations(self):
        """Historical context rejects create, update, delete, publish, close, grade, return, attachments."""
        # 1. Create a draft and published homework in active context first
        self.auth_membership(self.teacher_user, self.mb_teacher_a)
        hw_draft = Homework.objects.create(
            school=self.school_a, academic_year=self.year_a_curr, academic_term=self.term_2,
            teacher_assignment=self.assign_a, title='Draft HW',
            due_date=timezone.now() + timedelta(days=5), max_grade=Decimal('20.00'),
            created_by=self.teacher_user, status='draft',
        )
        hw_pub = Homework.objects.create(
            school=self.school_a, academic_year=self.year_a_curr, academic_term=self.term_2,
            teacher_assignment=self.assign_a, title='Published HW',
            due_date=timezone.now() + timedelta(days=5), max_grade=Decimal('20.00'),
            created_by=self.teacher_user, status='published', published_at=timezone.now(),
        )
        sub = HomeworkSubmission.objects.create(
            homework=hw_pub, student_enrollment=self.enrollments[0],
            status='submitted', submitted_at=timezone.now(), answer='Answer',
        )
        att = HomeworkAttachment.objects.create(
            homework=hw_draft,
            file=SimpleUploadedFile('test.txt', b'hello', content_type='text/plain'),
            original_name='test.txt', content_type='text/plain', file_size=5,
            uploaded_by=self.teacher_user,
        )

        # Switch to historical membership
        self.auth_membership(self.teacher_hist_user, self.mb_teacher_hist)

        # A. Create -> 403
        r_create = self.client.post('/api/v1/homework/', {
            'teacher_assignment': self.assign_a.pk,
            'title': 'Hist Create',
            'due_date': '2026-03-20T18:00:00Z',
        }, format='json')
        self.assertEqual(r_create.status_code, status.HTTP_403_FORBIDDEN)

        # B. Update -> 403
        r_update = self.client.patch(f'/api/v1/homework/{hw_draft.pk}/', {'title': 'Updated'}, format='json')
        self.assertEqual(r_update.status_code, status.HTTP_403_FORBIDDEN)

        # C. Publish -> 403
        r_publish = self.client.post(f'/api/v1/homework/{hw_draft.pk}/publish/')
        self.assertEqual(r_publish.status_code, status.HTTP_403_FORBIDDEN)

        # D. Close -> 403
        r_close = self.client.post(f'/api/v1/homework/{hw_pub.pk}/close/')
        self.assertEqual(r_close.status_code, status.HTTP_403_FORBIDDEN)

        # E. Attachment upload -> 403
        r_att_up = self.client.post(f'/api/v1/homework/{hw_draft.pk}/attachments/', {
            'files': [SimpleUploadedFile('a.txt', b'abc', content_type='text/plain')],
        }, format='multipart')
        self.assertEqual(r_att_up.status_code, status.HTTP_403_FORBIDDEN)

        # F. Attachment delete -> 403
        r_att_del = self.client.delete(f'/api/v1/homework/{hw_draft.pk}/attachments/{att.pk}/')
        self.assertEqual(r_att_del.status_code, status.HTTP_403_FORBIDDEN)

        # G. Grade -> 403
        r_grade = self.client.post(f'/api/v1/homework-submissions/{sub.pk}/grade/', {'grade': '18.00'}, format='json')
        self.assertEqual(r_grade.status_code, status.HTTP_403_FORBIDDEN)

        # H. Return -> 403
        r_return = self.client.post(f'/api/v1/homework-submissions/{sub.pk}/return/', {'teacher_note': 'Revise'}, format='json')
        self.assertEqual(r_return.status_code, status.HTTP_403_FORBIDDEN)

        # I. Delete draft -> 403
        r_del = self.client.delete(f'/api/v1/homework/{hw_draft.pk}/')
        self.assertEqual(r_del.status_code, status.HTTP_403_FORBIDDEN)

    # =========================================================================
    # 4. TEACHER WORK CENTER — STUDENT STATUS ENDPOINT
    # =========================================================================

    def test_10_homework_student_status_complete_projection(self):
        """student-status endpoint returns all target enrolled students with projection."""
        self.auth_membership(self.teacher_user, self.mb_teacher_a)
        hw = Homework.objects.create(
            school=self.school_a, academic_year=self.year_a_curr, academic_term=self.term_2,
            teacher_assignment=self.assign_a, title='Roster Test HW',
            due_date=timezone.now() + timedelta(days=3), max_grade=Decimal('20.00'),
            created_by=self.teacher_user, status='published', published_at=timezone.now(),
        )

        # Student 0: Draft
        HomeworkSubmission.objects.create(
            homework=hw, student_enrollment=self.enrollments[0],
            status='draft', answer='Draft answer',
        )
        # Student 1: Submitted
        HomeworkSubmission.objects.create(
            homework=hw, student_enrollment=self.enrollments[1],
            status='submitted', submitted_at=timezone.now(), answer='Final answer',
        )
        # Student 2: Graded
        HomeworkSubmission.objects.create(
            homework=hw, student_enrollment=self.enrollments[2],
            status='graded', submitted_at=timezone.now() - timedelta(hours=2),
            answer='Graded answer', grade=Decimal('19.50'),
            graded_by=self.teacher_user, graded_at=timezone.now() - timedelta(hours=1),
            teacher_note='Excellent',
        )
        # Student 3: Not started (no submission in DB)

        response = self.client.get(f'/api/v1/homework/{hw.pk}/student-status/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data

        # Check aggregate counts
        self.assertEqual(data['total_students'], 4)
        self.assertEqual(data['submitted_count'], 2)  # submitted + graded
        self.assertEqual(data['graded_count'], 1)
        self.assertEqual(data['draft_count'], 1)
        self.assertEqual(data['not_started_count'], 1)
        self.assertEqual(data['pending_grading_count'], 1)

        # Verify students list
        students = data['students']
        self.assertEqual(len(students), 4)

        status_map = {s['student_id']: s for s in students}

        # Student 0: draft
        s0 = status_map[self.students[0].pk]
        self.assertEqual(s0['status'], 'draft')
        self.assertFalse(s0['can_grade'])

        # Student 1: submitted
        s1 = status_map[self.students[1].pk]
        self.assertEqual(s1['status'], 'submitted')
        self.assertTrue(s1['can_grade'])
        self.assertTrue(s1['can_return'])

        # Student 2: graded
        s2 = status_map[self.students[2].pk]
        self.assertEqual(s2['status'], 'graded')
        self.assertEqual(s2['grade'], '19.50')
        self.assertEqual(s2['teacher_note'], 'Excellent')
        self.assertTrue(s2['can_return'])

        # Student 3: not_started
        s3 = status_map[self.students[3].pk]
        self.assertEqual(s3['status'], 'not_started')
        self.assertIsNone(s3['submission_id'])
        self.assertFalse(s3['can_grade'])
        self.assertFalse(s3['can_return'])

        # Check section 2 student is NOT present (no cross-section leakage)
        self.assertNotIn(self.stu_sec2.pk, status_map)

    def test_11_homework_student_status_filters_and_search(self):
        """student-status endpoint supports status and search query params."""
        self.auth_membership(self.teacher_user, self.mb_teacher_a)
        hw = Homework.objects.create(
            school=self.school_a, academic_year=self.year_a_curr, academic_term=self.term_2,
            teacher_assignment=self.assign_a, title='Search HW',
            due_date=timezone.now() + timedelta(days=3), max_grade=Decimal('20.00'),
            created_by=self.teacher_user, status='published', published_at=timezone.now(),
        )
        HomeworkSubmission.objects.create(
            homework=hw, student_enrollment=self.enrollments[0],
            status='submitted', submitted_at=timezone.now(), answer='A',
        )

        # Filter by status=not_started -> 3 students
        r_ns = self.client.get(f'/api/v1/homework/{hw.pk}/student-status/?status=not_started')
        self.assertEqual(r_ns.status_code, status.HTTP_200_OK)
        self.assertEqual(len(r_ns.data['students']), 3)

        # Filter by status=submitted -> 1 student
        r_sub = self.client.get(f'/api/v1/homework/{hw.pk}/student-status/?status=submitted')
        self.assertEqual(r_sub.status_code, status.HTTP_200_OK)
        self.assertEqual(len(r_sub.data['students']), 1)
        self.assertEqual(r_sub.data['students'][0]['student_id'], self.students[0].pk)

        # Search by student code
        r_srch = self.client.get(f'/api/v1/homework/{hw.pk}/student-status/?search=STU-1002')
        self.assertEqual(r_srch.status_code, status.HTTP_200_OK)
        self.assertEqual(len(r_srch.data['students']), 1)
        self.assertEqual(r_srch.data['students'][0]['student_id'], self.students[1].pk)

    # =========================================================================
    # 5. FILTERS HARDENING
    # =========================================================================

    def test_12_homework_filters_graded_and_pending_grading(self):
        """_filter_homework correctly handles graded and pending_grading query params."""
        self.auth_membership(self.teacher_user, self.mb_teacher_a)
        hw_pending = Homework.objects.create(
            school=self.school_a, academic_year=self.year_a_curr, academic_term=self.term_2,
            teacher_assignment=self.assign_a, title='Needs Grading HW',
            due_date=timezone.now() + timedelta(days=3), max_grade=Decimal('20.00'),
            created_by=self.teacher_user, status='published', published_at=timezone.now(),
        )
        HomeworkSubmission.objects.create(
            homework=hw_pending, student_enrollment=self.enrollments[0],
            status='submitted', submitted_at=timezone.now(), answer='Sub',
        )

        hw_graded = Homework.objects.create(
            school=self.school_a, academic_year=self.year_a_curr, academic_term=self.term_2,
            teacher_assignment=self.assign_a, title='All Graded HW',
            due_date=timezone.now() + timedelta(days=3), max_grade=Decimal('20.00'),
            created_by=self.teacher_user, status='published', published_at=timezone.now(),
        )
        HomeworkSubmission.objects.create(
            homework=hw_graded, student_enrollment=self.enrollments[0],
            status='graded', submitted_at=timezone.now(), answer='Sub',
            grade=Decimal('15.00'), graded_by=self.teacher_user, graded_at=timezone.now(),
        )

        # Filter pending_grading=true
        r_pending = self.client.get('/api/v1/homework/?pending_grading=true')
        self.assertEqual(r_pending.status_code, status.HTTP_200_OK)
        ids_pending = [row['id'] for row in r_pending.data['results']]
        self.assertIn(hw_pending.pk, ids_pending)
        self.assertNotIn(hw_graded.pk, ids_pending)

        # Filter graded=true
        r_graded = self.client.get('/api/v1/homework/?graded=true')
        self.assertEqual(r_graded.status_code, status.HTTP_200_OK)
        ids_graded = [row['id'] for row in r_graded.data['results']]
        self.assertIn(hw_graded.pk, ids_graded)
        self.assertNotIn(hw_pending.pk, ids_graded)
