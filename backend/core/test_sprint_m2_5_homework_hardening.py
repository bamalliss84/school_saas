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
    Parent,
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
    return_submission,
    review_submission,
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

        # 8. Parent in School A for Student 1
        cls.parent_user = User.objects.create_user(
            username='parent_1',
            email='parent1@saas.local',
            password=cls.password,
            first_name='Parent1',
            last_name='Test',
            role='parent',
            school=cls.school_a,
            academic_year=cls.year_a_curr,
        )
        cls.parent_a = Parent.objects.create(
            school=cls.school_a,
            user=cls.parent_user,
            full_name='Parent 1 Test',
        )
        cls.mb_parent_a = SchoolMembership.objects.create(
            user=cls.parent_user, school=cls.school_a, role='parent', status='active', is_default=True,
        )
        StudentGuardian.objects.create(
            student=cls.students[0],
            parent=cls.parent_a,
            relationship='father',
            is_primary=True,
            can_receive_notifications=True,
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

    # =========================================================================
    # 6. UNGRADED HOMEWORK REVIEW LIFECYCLE & CONTRACT
    # =========================================================================

    def test_13_ungraded_submitted_can_be_reviewed_and_stores_teacher_note_with_null_grade(self):
        """Ungraded homework submission transitions from submitted to reviewed via /review/."""
        self.auth_membership(self.teacher_user, self.mb_teacher_a)
        hw = Homework.objects.create(
            school=self.school_a, academic_year=self.year_a_curr, academic_term=self.term_2,
            teacher_assignment=self.assign_a, title='Formative Reading HW',
            due_date=timezone.now() + timedelta(days=5), max_grade=None,
            created_by=self.teacher_user, status='published', published_at=timezone.now(),
        )
        sub = HomeworkSubmission.objects.create(
            homework=hw, student_enrollment=self.enrollments[0],
            status='submitted', submitted_at=timezone.now(), answer='Reading completed.',
        )

        res = self.client.post(
            f'/api/v1/homework-submissions/{sub.pk}/review/',
            {'teacher_note': 'Excellent effort on reading notes!'},
            format='json',
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['status'], 'reviewed')
        self.assertIsNone(res.data['grade'])
        self.assertEqual(res.data['teacher_note'], 'Excellent effort on reading notes!')
        self.assertFalse(res.data['can_edit'])
        self.assertFalse(res.data['can_submit'])
        self.assertFalse(res.data['can_grade'])

        sub.refresh_from_db()
        self.assertEqual(sub.status, 'reviewed')
        self.assertIsNone(sub.grade)
        self.assertEqual(sub.teacher_note, 'Excellent effort on reading notes!')
        self.assertEqual(sub.graded_by, self.teacher_user)
        self.assertIsNotNone(sub.graded_at)

    def test_14_graded_homework_cannot_use_review_action(self):
        """Graded homework submission rejects /review/ with HTTP 400."""
        self.auth_membership(self.teacher_user, self.mb_teacher_a)
        hw = Homework.objects.create(
            school=self.school_a, academic_year=self.year_a_curr, academic_term=self.term_2,
            teacher_assignment=self.assign_a, title='Graded Math HW',
            due_date=timezone.now() + timedelta(days=5), max_grade=Decimal('10.00'),
            created_by=self.teacher_user, status='published', published_at=timezone.now(),
        )
        sub = HomeworkSubmission.objects.create(
            homework=hw, student_enrollment=self.enrollments[0],
            status='submitted', submitted_at=timezone.now(), answer='Solutions',
        )

        res = self.client.post(
            f'/api/v1/homework-submissions/{sub.pk}/review/',
            {'teacher_note': 'Feedback'},
            format='json',
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('This homework is graded. Use the grade action instead.', str(res.data))

    def test_15_ungraded_homework_cannot_use_grade_action(self):
        """Ungraded homework submission rejects /grade/ with HTTP 400."""
        self.auth_membership(self.teacher_user, self.mb_teacher_a)
        hw = Homework.objects.create(
            school=self.school_a, academic_year=self.year_a_curr, academic_term=self.term_2,
            teacher_assignment=self.assign_a, title='Ungraded Notes HW',
            due_date=timezone.now() + timedelta(days=5), max_grade=None,
            created_by=self.teacher_user, status='published', published_at=timezone.now(),
        )
        sub = HomeworkSubmission.objects.create(
            homework=hw, student_enrollment=self.enrollments[0],
            status='submitted', submitted_at=timezone.now(), answer='Notes',
        )

        res = self.client.post(
            f'/api/v1/homework-submissions/{sub.pk}/grade/',
            {'grade': '8.00', 'teacher_note': 'Good'},
            format='json',
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('This homework is not graded.', str(res.data))

    def test_16_review_permission_and_isolation(self):
        """Only authorized teachers/admins in active context can review submissions."""
        hw = Homework.objects.create(
            school=self.school_a, academic_year=self.year_a_curr, academic_term=self.term_2,
            teacher_assignment=self.assign_a, title='Ungraded HW',
            due_date=timezone.now() + timedelta(days=5), max_grade=None,
            created_by=self.teacher_user, status='published', published_at=timezone.now(),
        )
        sub = HomeworkSubmission.objects.create(
            homework=hw, student_enrollment=self.enrollments[0],
            status='submitted', submitted_at=timezone.now(), answer='Notes',
        )

        # 1. Unrelated teacher (Teacher B in School B context) -> 404
        self.auth_membership(self.teacher_b_user, self.mb_teacher_b_user)
        res_b = self.client.post(f'/api/v1/homework-submissions/{sub.pk}/review/', {}, format='json')
        self.assertEqual(res_b.status_code, status.HTTP_404_NOT_FOUND)

        # 2. Student cannot review -> 403
        mb_stu = SchoolMembership.objects.get(user=self.student_users[0], school=self.school_a)
        self.auth_membership(self.student_users[0], mb_stu)
        res_stu = self.client.post(f'/api/v1/homework-submissions/{sub.pk}/review/', {}, format='json')
        self.assertEqual(res_stu.status_code, status.HTTP_403_FORBIDDEN)

        # 3. Historical context teacher -> 403 (require_writable_context)
        self.auth_membership(self.teacher_hist_user, self.mb_teacher_hist)
        res_hist = self.client.post(f'/api/v1/homework-submissions/{sub.pk}/review/', {}, format='json')
        self.assertEqual(res_hist.status_code, status.HTTP_403_FORBIDDEN)

    def test_17_reviewed_submission_cannot_be_edited_or_submitted_by_student(self):
        """Reviewed submission is locked against student answer updates, final-submit, and attachments."""
        hw = Homework.objects.create(
            school=self.school_a, academic_year=self.year_a_curr, academic_term=self.term_2,
            teacher_assignment=self.assign_a, title='Locked Reviewed HW',
            due_date=timezone.now() + timedelta(days=5), max_grade=None,
            created_by=self.teacher_user, status='published', published_at=timezone.now(),
        )
        sub = HomeworkSubmission.objects.create(
            homework=hw, student_enrollment=self.enrollments[0],
            status='reviewed', submitted_at=timezone.now(), answer='Initial Answer',
            graded_by=self.teacher_user, graded_at=timezone.now(),
        )

        mb_stu = SchoolMembership.objects.get(user=self.student_users[0], school=self.school_a)
        self.auth_membership(self.student_users[0], mb_stu)

        # Attempt to edit answer -> 400
        res_patch = self.client.patch(
            f'/api/v1/homework-submissions/{sub.pk}/',
            {'answer': 'Modified Answer'},
            format='json',
        )
        self.assertEqual(res_patch.status_code, status.HTTP_400_BAD_REQUEST)

        # Attempt to final-submit -> 400
        res_submit = self.client.post(
            f'/api/v1/homework-submissions/{sub.pk}/final-submit/',
            {},
            format='json',
        )
        self.assertEqual(res_submit.status_code, status.HTTP_400_BAD_REQUEST)

        # Attempt to add attachment -> 400
        file_obj = SimpleUploadedFile('doc.pdf', b'%PDF-1.4 test', content_type='application/pdf')
        res_att = self.client.post(
            f'/api/v1/homework-submissions/{sub.pk}/attachments/',
            {'files': [file_obj]},
            format='multipart',
        )
        self.assertEqual(res_att.status_code, status.HTTP_400_BAD_REQUEST)

    def test_18_reviewed_can_be_returned_and_resubmitted_and_rereviewed(self):
        """Teacher can return a reviewed submission; student can revise, resubmit, and teacher can re-review."""
        hw = Homework.objects.create(
            school=self.school_a, academic_year=self.year_a_curr, academic_term=self.term_2,
            teacher_assignment=self.assign_a, title='Iterative Formative HW',
            due_date=timezone.now() + timedelta(days=5), max_grade=None,
            created_by=self.teacher_user, status='published', published_at=timezone.now(),
        )
        sub = HomeworkSubmission.objects.create(
            homework=hw, student_enrollment=self.enrollments[0],
            status='reviewed', submitted_at=timezone.now(), answer='Draft 1',
            graded_by=self.teacher_user, graded_at=timezone.now(),
        )

        # 1. Teacher returns reviewed submission
        self.auth_membership(self.teacher_user, self.mb_teacher_a)
        res_ret = self.client.post(
            f'/api/v1/homework-submissions/{sub.pk}/return/',
            {'teacher_note': 'Please expand chapter 2 summary.'},
            format='json',
        )
        self.assertEqual(res_ret.status_code, status.HTTP_200_OK)
        self.assertEqual(res_ret.data['status'], 'returned')
        self.assertEqual(res_ret.data['teacher_note'], 'Please expand chapter 2 summary.')

        # 2. Student edits and resubmits
        mb_stu = SchoolMembership.objects.get(user=self.student_users[0], school=self.school_a)
        self.auth_membership(self.student_users[0], mb_stu)
        res_edit = self.client.patch(
            f'/api/v1/homework-submissions/{sub.pk}/',
            {'answer': 'Draft 2 with expanded chapter 2.'},
            format='json',
        )
        self.assertEqual(res_edit.status_code, status.HTTP_200_OK)
        res_sub = self.client.post(f'/api/v1/homework-submissions/{sub.pk}/final-submit/', {}, format='json')
        self.assertEqual(res_sub.status_code, status.HTTP_200_OK)
        self.assertEqual(res_sub.data['status'], 'submitted')

        # 3. Teacher reviews revised submission
        self.auth_membership(self.teacher_user, self.mb_teacher_a)
        res_rev2 = self.client.post(
            f'/api/v1/homework-submissions/{sub.pk}/review/',
            {'teacher_note': 'Much better, approved!'},
            format='json',
        )
        self.assertEqual(res_rev2.status_code, status.HTTP_200_OK)
        self.assertEqual(res_rev2.data['status'], 'reviewed')
        self.assertEqual(res_rev2.data['teacher_note'], 'Much better, approved!')

    def test_19_student_status_roster_projection_for_ungraded_homework(self):
        """Student-status roster correctly reflects can_review, reviewed_count, and reviewed filtering."""
        self.auth_membership(self.teacher_user, self.mb_teacher_a)
        hw = Homework.objects.create(
            school=self.school_a, academic_year=self.year_a_curr, academic_term=self.term_2,
            teacher_assignment=self.assign_a, title='Roster Ungraded HW',
            due_date=timezone.now() + timedelta(days=5), max_grade=None,
            created_by=self.teacher_user, status='published', published_at=timezone.now(),
        )
        # Student 0 submitted, Student 1 reviewed, Students 2 & 3 not started
        sub0 = HomeworkSubmission.objects.create(
            homework=hw, student_enrollment=self.enrollments[0],
            status='submitted', submitted_at=timezone.now(), answer='Sub 0',
        )
        sub1 = HomeworkSubmission.objects.create(
            homework=hw, student_enrollment=self.enrollments[1],
            status='reviewed', submitted_at=timezone.now(), answer='Sub 1',
            teacher_note='Well done', graded_by=self.teacher_user, graded_at=timezone.now(),
        )

        res = self.client.get(f'/api/v1/homework/{hw.pk}/student-status/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['total_students'], 4)
        self.assertEqual(res.data['submitted_count'], 2)
        self.assertEqual(res.data['reviewed_count'], 1)
        self.assertEqual(res.data['graded_count'], 0)
        self.assertEqual(res.data['not_started_count'], 2)

        students_map = {s['student_id']: s for s in res.data['students']}
        # Student 0 (submitted): can_review=True, can_grade=False, can_return=True
        s0 = students_map[self.students[0].pk]
        self.assertEqual(s0['status'], 'submitted')
        self.assertTrue(s0['can_review'])
        self.assertFalse(s0['can_grade'])
        self.assertTrue(s0['can_return'])

        # Student 1 (reviewed): can_review=False, can_grade=False, can_return=True
        s1 = students_map[self.students[1].pk]
        self.assertEqual(s1['status'], 'reviewed')
        self.assertFalse(s1['can_review'])
        self.assertFalse(s1['can_grade'])
        self.assertTrue(s1['can_return'])
        self.assertEqual(s1['teacher_note'], 'Well done')

        # Filter by status=reviewed -> 1 student
        res_filt = self.client.get(f'/api/v1/homework/{hw.pk}/student-status/?status=reviewed')
        self.assertEqual(res_filt.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res_filt.data['students']), 1)
        self.assertEqual(res_filt.data['students'][0]['student_id'], self.students[1].pk)

    def test_20_completion_status_and_visibility_for_student_and_parent(self):
        """Student and linked parent can view reviewed completion_status and teacher_note."""
        hw = Homework.objects.create(
            school=self.school_a, academic_year=self.year_a_curr, academic_term=self.term_2,
            teacher_assignment=self.assign_a, title='Visibility HW',
            due_date=timezone.now() + timedelta(days=5), max_grade=None,
            created_by=self.teacher_user, status='published', published_at=timezone.now(),
        )
        sub = HomeworkSubmission.objects.create(
            homework=hw, student_enrollment=self.enrollments[0],
            status='reviewed', submitted_at=timezone.now(), answer='Student answer',
            teacher_note='Formative feedback note for student and parent.',
            graded_by=self.teacher_user, graded_at=timezone.now(),
        )

        # 1. Student view
        mb_stu = SchoolMembership.objects.get(user=self.student_users[0], school=self.school_a)
        self.auth_membership(self.student_users[0], mb_stu)
        res_stu = self.client.get('/api/v1/students/me/homework/')
        self.assertEqual(res_stu.status_code, status.HTTP_200_OK)
        hw_row = next(r for r in res_stu.data['results'] if r['id'] == hw.pk)
        self.assertEqual(hw_row['completion_status'], 'reviewed')
        self.assertEqual(hw_row['submission_status'], 'reviewed')
        self.assertEqual(hw_row['teacher_note'], 'Formative feedback note for student and parent.')
        self.assertFalse(hw_row['can_edit'])
        self.assertFalse(hw_row['can_submit'])
        self.assertFalse(hw_row['can_final_submit'])

        # 2. Parent view
        self.auth_membership(self.parent_user, self.mb_parent_a)
        res_par = self.client.get(f'/api/v1/parents/me/children/{self.students[0].pk}/homework/')
        self.assertEqual(res_par.status_code, status.HTTP_200_OK)
        par_row = next(r for r in res_par.data['results'] if r['id'] == hw.pk)
        self.assertEqual(par_row['submission_status'], 'reviewed')
        self.assertEqual(par_row['teacher_note'], 'Formative feedback note for student and parent.')

        # 3. Direct submission detail view by parent
        res_sub_par = self.client.get(f'/api/v1/homework-submissions/{sub.pk}/')
        self.assertEqual(res_sub_par.status_code, status.HTTP_200_OK)
        self.assertEqual(res_sub_par.data['status'], 'reviewed')
        self.assertEqual(res_sub_par.data['teacher_note'], 'Formative feedback note for student and parent.')

    def test_21_homework_and_class_summaries_include_reviewed_status(self):
        """Summary endpoints accurately count reviewed submissions and factor them into completion."""
        self.auth_membership(self.teacher_user, self.mb_teacher_a)
        hw = Homework.objects.create(
            school=self.school_a, academic_year=self.year_a_curr, academic_term=self.term_2,
            teacher_assignment=self.assign_a, title='Summary HW',
            due_date=timezone.now() + timedelta(days=5), max_grade=None,
            created_by=self.teacher_user, status='published', published_at=timezone.now(),
        )
        HomeworkSubmission.objects.create(
            homework=hw, student_enrollment=self.enrollments[0],
            status='reviewed', submitted_at=timezone.now(), answer='Answer 1',
            teacher_note='Good job', graded_by=self.teacher_user, graded_at=timezone.now(),
        )
        HomeworkSubmission.objects.create(
            homework=hw, student_enrollment=self.enrollments[1],
            status='submitted', submitted_at=timezone.now(), answer='Answer 2',
        )

        # 1. Homework summary endpoint
        res_hw_sum = self.client.get(f'/api/v1/homework/{hw.pk}/summary/')
        self.assertEqual(res_hw_sum.status_code, status.HTTP_200_OK)
        self.assertEqual(res_hw_sum.data['reviewed'], 1)
        self.assertEqual(res_hw_sum.data['submitted'], 1)
        self.assertEqual(res_hw_sum.data['target_students'], 4)
        # completion_rate = (1 submitted + 1 reviewed) / 4 = 50.0%
        self.assertEqual(res_hw_sum.data['completion_rate'], 50.0)

        # 2. Student summary report endpoint
        res_stu_sum = self.client.get(f'/api/v1/homework/student/{self.students[0].pk}/summary/')
        self.assertEqual(res_stu_sum.status_code, status.HTTP_200_OK)
        self.assertEqual(res_stu_sum.data['statistics']['reviewed'], 1)

        # 3. Classroom summary report endpoint
        res_cls_sum = self.client.get(f'/api/v1/homework/class/{self.class_10a.pk}/summary/')
        self.assertEqual(res_cls_sum.status_code, status.HTTP_200_OK)
        self.assertEqual(res_cls_sum.data['statistics']['reviewed'], 1)

    def test_22_active_context_authority_enforced_in_submission_and_review(self):
        """Multi-role user authority is derived strictly from active membership context, not legacy user.role."""
        mb_teacher_b_multirole = SchoolMembership.objects.create(
            user=self.multirole_user, school=self.school_b, role='teacher', status='active', is_default=False,
        )
        hw = Homework.objects.create(
            school=self.school_a, academic_year=self.year_a_curr, academic_term=self.term_2,
            teacher_assignment=self.assign_a, title='Multi-Role Authority Test HW',
            due_date=timezone.now() + timedelta(days=5), max_grade=None,
            created_by=self.teacher_user, status='published', published_at=timezone.now(),
        )
        sub = HomeworkSubmission.objects.create(
            homework=hw, student_enrollment=self.enrollments[0],
            status='submitted', submitted_at=timezone.now(), answer='Active context check',
        )

        # 1. School B Teacher context: cannot review School A homework even though user.role=='school_admin' -> 404
        self.auth_membership(self.multirole_user, mb_teacher_b_multirole)
        res_b = self.client.post(
            f'/api/v1/homework-submissions/{sub.pk}/review/',
            {'teacher_note': 'Attempt from School B'},
            format='json',
        )
        self.assertEqual(res_b.status_code, status.HTTP_404_NOT_FOUND)

        # 2. Switch to School A Admin context: active context authorizes review
        self.auth_membership(self.multirole_user, self.mb_admin_a)
        res_a = self.client.post(
            f'/api/v1/homework-submissions/{sub.pk}/review/',
            {'teacher_note': 'Approved by School A Admin'},
            format='json',
        )
        self.assertEqual(res_a.status_code, status.HTTP_200_OK)
        self.assertEqual(res_a.data['status'], 'reviewed')
        self.assertEqual(res_a.data['teacher_note'], 'Approved by School A Admin')
