from datetime import date, datetime, time, timedelta
from decimal import Decimal

from django.conf import settings
from django.contrib.auth.hashers import make_password
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from core.models import (
    AcademicTerm, AcademicYear, Announcement, AnnouncementReceipt, Attendance,
    Classroom, ClassSubject, Conversation, ConversationParticipant, Exam, ExamResult, ExamType, Homework,
    HomeworkSubmission, Notification, Parent, School, SchoolMembership,
    SchoolSetting, Section, Student, StudentEnrollment, StudentGuardian,
    Subject, Teacher, TeacherAssignment, User, Message,
    SchoolPeriod, SchoolTimetableConfig, TimetableEntry,
)


DEMO_PASSWORD = 'DemoPass123!'
DEMO_SCHOOL_CODES = ('DEMO_NOOR', 'DEMO_FUTURE')


class Command(BaseCommand):
    help = 'Create deterministic development-only School SaaS demo data.'

    def add_arguments(self, parser):
        parser.add_argument('--reset-demo', action='store_true')
        parser.add_argument(
            '--allow-non-debug', action='store_true',
            help='Explicitly acknowledge seeding a non-DEBUG non-production environment.',
        )

    def handle(self, *args, **options):
        if not settings.DEBUG and not options['allow_non_debug']:
            raise CommandError(
                'Demo seeding is disabled when DEBUG=False. Use --allow-non-debug only '
                'in an isolated acceptance environment.',
            )
        with transaction.atomic():
            if options['reset_demo']:
                self._reset_demo()
            summary = self._seed()
        self.stdout.write(self.style.SUCCESS(
            'Demo dataset ready: '
            f"{summary['schools']} schools, {summary['students']} students, "
            f"{summary['attendance']} attendance rows, "
            f"{summary['published_results']} published result rows.",
        ))

    def _reset_demo(self):
        TimetableEntry.objects.filter(school__code__in=DEMO_SCHOOL_CODES).delete()
        Announcement.objects.filter(school__code__in=DEMO_SCHOOL_CODES).delete()
        Conversation.objects.filter(school__code__in=DEMO_SCHOOL_CODES).delete()
        ExamResult.objects.filter(exam__school__code__in=DEMO_SCHOOL_CODES).delete()
        School.objects.filter(code__in=DEMO_SCHOOL_CODES).delete()
        User.objects.filter(username__startswith='demo_').delete()

    def _user(self, username, *, role, school=None, year=None, superuser=False):
        defaults = {
            'email': f'{username}@example.com',
            'role': role,
            'school': school,
            'academic_year': year,
            'is_active': True,
            'is_active_school_user': True,
            'is_staff': superuser,
            'is_superuser': superuser,
        }
        user = User.objects.filter(username=username).first()
        if user is None:
            user = User(username=username, password=make_password(DEMO_PASSWORD), **defaults)
        else:
            for field, value in defaults.items():
                setattr(user, field, value)
            user.set_password(DEMO_PASSWORD)
        user.save()
        return user

    def _membership(self, user, school, role, *, status='active', default=False):
        membership, _ = SchoolMembership.objects.update_or_create(
            user=user, school=school, role=role,
            defaults={'status': status, 'is_default': default},
        )
        return membership

    def _school_structure(self, code, name):
        school, _ = School.objects.update_or_create(
            code=code,
            defaults={
                'name': name, 'is_active': True,
                'email': f'{code.lower()}@example.com', 'phone': '0500000000',
                'address': 'DEMO address only',
            },
        )
        SchoolSetting.objects.update_or_create(
            school=school,
            defaults={
                'school_name_ar': name, 'school_name_en': f'{code} Demo School',
                'timezone': 'Asia/Aden', 'language': 'ar',
            },
        )
        today = timezone.localdate()
        current_start_year = today.year if today.month >= 9 else today.year - 1
        prev_start_year = current_start_year - 1

        years = {}
        for key, year_name, start, end, active in (
            ('previous', f'DEMO {prev_start_year}/{prev_start_year + 1}', date(prev_start_year, 9, 1), date(prev_start_year + 1, 8, 31), False),
            ('current', f'DEMO {current_start_year}/{current_start_year + 1}', date(current_start_year, 9, 1), date(current_start_year + 1, 8, 31), True),
        ):
            years[key], _ = AcademicYear.objects.update_or_create(
                school=school, name=year_name,
                defaults={'start_date': start, 'end_date': end, 'is_active': active},
            )

        terms = {}
        # Previous Year Term 1
        terms['previous'], _ = AcademicTerm.objects.update_or_create(
            school=school, academic_year=years['previous'], term_type='term_1',
            defaults={
                'name': 'DEMO Term 1 previous',
                'start_date': date(prev_start_year, 9, 1),
                'end_date': date(prev_start_year, 12, 31),
                'is_active': False,
            },
        )

        # Current Year Terms (Term 1: Sept-Dec, Term 2: Jan-Apr, Term 3: May-Aug)
        current_year = years['current']
        term_defs = (
            ('current', 'term_1', 'DEMO Term 1 current', date(current_start_year, 9, 1), date(current_start_year, 12, 31)),
            ('current_2', 'term_2', 'DEMO Term 2 current', date(current_start_year + 1, 1, 1), date(current_start_year + 1, 4, 30)),
            ('current_3', 'term_3', 'DEMO Term 3 current', date(current_start_year + 1, 5, 1), date(current_start_year + 1, 8, 31)),
        )
        active_term_found = False
        for term_key, term_type, term_name, start_d, end_d in term_defs:
            is_active_term = (start_d <= today <= end_d)
            if is_active_term:
                active_term_found = True
            terms[term_key], _ = AcademicTerm.objects.update_or_create(
                school=school, academic_year=current_year, term_type=term_type,
                defaults={
                    'name': term_name,
                    'start_date': start_d,
                    'end_date': end_d,
                    'is_active': is_active_term,
                },
            )

        # Guarantee exactly one term is marked active for current year
        if not active_term_found:
            terms['current'].is_active = True
            terms['current'].save(update_fields=['is_active'])

        active_term_pk = next(terms[k].pk for k in ('current', 'current_2', 'current_3') if terms[k].is_active)
        AcademicTerm.objects.filter(
            school=school, academic_year=current_year,
        ).exclude(pk=active_term_pk).update(is_active=False)
        classrooms, sections = {}, {}
        for year_key, year in years.items():
            for grade in (6, 7):
                classroom, _ = Classroom.objects.update_or_create(
                    school=school, academic_year=year, code=f'DEMO_G{grade}',
                    defaults={'name': f'DEMO Grade {grade}', 'is_active': True},
                )
                classrooms[(year_key, grade)] = classroom
                for section_code in ('A', 'B'):
                    section, _ = Section.objects.update_or_create(
                        school=school, academic_year=year, classroom=classroom,
                        code=f'DEMO_{section_code}',
                        defaults={'name': f'DEMO Section {section_code}', 'is_active': True},
                    )
                    sections[(year_key, grade, section_code)] = section
        subjects = {}
        for code_suffix, name_en in (
            ('MATH', 'Mathematics'), ('AR', 'Arabic'),
            ('SCI', 'Science'), ('EN', 'English'),
        ):
            subject, _ = Subject.objects.update_or_create(
                school=school, code=f'DEMO_{code_suffix}',
                defaults={'name': f'DEMO {name_en}', 'is_active': True},
            )
            subjects[code_suffix] = subject
            for (year_key, _grade), classroom in classrooms.items():
                ClassSubject.objects.update_or_create(
                    school=school, academic_year=years[year_key],
                    classroom=classroom, subject=subject,
                    defaults={'weekly_periods': 4},
                )
        for code_suffix, label, maximum, weight in (
            ('QUIZ', 'اختبار قصير', 20, 10),
            ('MONTHLY', 'اختبار شهري', 20, 10),
            ('MID', 'اختبار منتصف الفصل', 50, 25),
            ('TERM', 'اختبار فصلي', 30, 25),
            ('FINAL', 'اختبار نهائي', 100, 30),
        ):
            ExamType.objects.update_or_create(
                school=school, code=f'DEMO_{code_suffix}',
                defaults={
                    'name': f'DEMO {label}', 'max_score': Decimal(maximum),
                    'weight_percentage': Decimal(weight), 'is_active': True,
                },
            )
        return {
            'school': school, 'years': years, 'terms': terms,
            'classrooms': classrooms, 'sections': sections, 'subjects': subjects,
        }

    def _seed(self):
        a = self._school_structure('DEMO_NOOR', 'مدرسة النور التجريبية')
        b = self._school_structure('DEMO_FUTURE', 'مدرسة المستقبل التجريبية')
        school_a, school_b = a['school'], b['school']
        year_a, year_b = a['years']['current'], b['years']['current']

        super_admin = self._user('demo_super_admin', role='super_admin', superuser=True)
        admin_a = self._user('demo_school_a_admin', role='school_admin', school=school_a, year=year_a)
        admin_b = self._user('demo_school_b_admin', role='school_admin', school=school_b, year=year_b)
        teacher_a_user = self._user('demo_teacher_a', role='teacher', school=school_a, year=year_a)
        teacher_b_user = self._user('demo_teacher_b', role='teacher', school=school_b, year=year_b)
        multi_user = self._user('demo_teacher_multi', role='teacher', school=school_a, year=year_a)
        self._membership(admin_a, school_a, 'school_admin', default=True)
        self._membership(admin_b, school_b, 'school_admin', default=True)
        teacher_a_m = self._membership(teacher_a_user, school_a, 'teacher', default=True)
        self._membership(teacher_b_user, school_b, 'teacher', default=True)
        multi_a = self._membership(multi_user, school_a, 'teacher', default=True)
        self._membership(multi_user, school_b, 'teacher')

        teacher_a, _ = Teacher.objects.update_or_create(
            user=teacher_a_user,
            defaults={
                'school': school_a, 'academic_year': year_a, 'full_name': 'DEMO Teacher A',
                'employee_code': 'DEMO_TA',
            },
        )
        teacher_b, _ = Teacher.objects.update_or_create(
            user=teacher_b_user,
            defaults={
                'school': school_b, 'academic_year': year_b, 'full_name': 'DEMO Teacher B',
                'employee_code': 'DEMO_TB',
            },
        )
        teacher_multi, _ = Teacher.objects.update_or_create(
            user=multi_user,
            defaults={
                'school': school_a, 'academic_year': year_a,
                'full_name': 'DEMO Multi School Teacher', 'employee_code': 'DEMO_TM',
            },
        )
        assignment_specs = (
            ('a_math', teacher_a, a, 6, 'A', 'MATH'),
            ('a_arabic_g6', teacher_a, a, 6, 'A', 'AR'),
            ('a_science_g6', teacher_a, a, 6, 'A', 'SCI'),
            ('a_science', teacher_multi, a, 7, 'A', 'SCI'),
            ('b_math', teacher_multi, b, 6, 'B', 'MATH'),
            ('b_english', teacher_b, b, 7, 'A', 'EN'),
        )
        assignments = {}
        for key, teacher, structure, grade, section_code, subject_code in assignment_specs:
            assignments[key], _ = TeacherAssignment.objects.update_or_create(
                teacher=teacher, academic_year=structure['years']['current'],
                classroom=structure['classrooms'][('current', grade)],
                section=structure['sections'][('current', grade, section_code)],
                subject=structure['subjects'][subject_code],
                defaults={'school': structure['school'], 'is_current': True},
            )
        assignments['a_math_previous'], _ = TeacherAssignment.objects.update_or_create(
            teacher=teacher_a, academic_year=a['years']['previous'],
            classroom=a['classrooms'][('previous', 6)],
            section=a['sections'][('previous', 6, 'A')], subject=a['subjects']['MATH'],
            defaults={'school': school_a, 'is_current': True},
        )

        periods = {}
        for label, structure in (('a', a), ('b', b)):
            SchoolTimetableConfig.objects.update_or_create(
                school=structure['school'], academic_year=structure['years']['current'],
                defaults={'working_days': [0, 1, 2, 3, 4]},
            )
            for sequence, name, start, end, kind in (
                (1, 'DEMO First Lesson', time(7, 0), time(7, 45), 'lesson'),
                (2, 'DEMO Second Lesson', time(7, 50), time(8, 35), 'lesson'),
                (3, 'DEMO Break', time(8, 35), time(8, 55), 'break'),
                (4, 'DEMO Third Lesson', time(8, 55), time(9, 40), 'lesson'),
            ):
                periods[(label, sequence)], _ = SchoolPeriod.objects.update_or_create(
                    school=structure['school'], academic_year=structure['years']['current'],
                    sequence=sequence,
                    defaults={
                        'name': name, 'start_time': start, 'end_time': end,
                        'kind': kind, 'is_active': True,
                    },
                )
        SchoolTimetableConfig.objects.update_or_create(
            school=school_a, academic_year=a['years']['previous'],
            defaults={'working_days': [0, 1, 2, 3, 4]},
        )
        historical_period, _ = SchoolPeriod.objects.update_or_create(
            school=school_a, academic_year=a['years']['previous'], sequence=1,
            defaults={
                'name': 'DEMO Historical First Lesson', 'start_time': time(7, 0),
                'end_time': time(7, 45), 'kind': 'lesson', 'is_active': True,
            },
        )
        for key, assignment, period, weekday, room in (
            ('a_math_sun', assignments['a_math'], periods[('a', 1)], 0, 'DEMO Room A1'),
            ('a_science_sun', assignments['a_science'], periods[('a', 2)], 0, 'DEMO Lab A'),
            ('a_science_mon', assignments['a_science'], periods[('a', 1)], 1, 'DEMO Lab A'),
            ('b_math_sun', assignments['b_math'], periods[('b', 1)], 0, 'DEMO Room B1'),
            ('b_english_sun', assignments['b_english'], periods[('b', 2)], 0, 'DEMO Room B2'),
            ('b_math_mon', assignments['b_math'], periods[('b', 2)], 1, 'DEMO Room B1'),
        ):
            TimetableEntry.objects.update_or_create(
                school=assignment.school, academic_year=assignment.academic_year,
                teacher_assignment=assignment, weekday=weekday, period=period,
                valid_from=None, valid_to=None,
                defaults={
                    'room_or_location': room, 'is_active': True,
                    'created_by': admin_a if assignment.school_id == school_a.pk else admin_b,
                },
            )
        TimetableEntry.objects.update_or_create(
            school=school_a, academic_year=a['years']['previous'],
            teacher_assignment=assignments['a_math_previous'], weekday=0,
            period=historical_period, valid_from=None, valid_to=None,
            defaults={
                'room_or_location': 'DEMO Historical Room', 'is_active': True,
                'created_by': admin_a,
            },
        )

        parents = {}
        for username, structure in (('demo_parent_a', a), ('demo_parent_multi', b)):
            user = self._user(
                username, role='parent', school=structure['school'],
                year=structure['years']['current'],
            )
            parents[username], _ = Parent.objects.update_or_create(
                user=user,
                defaults={
                    'school': structure['school'], 'full_name': username.replace('_', ' ').title(),
                    'email': f'{username}@example.com', 'phone': '0500000001',
                },
            )
            self._membership(user, structure['school'], 'parent', default=True)

        enrollments = []
        students = []
        for structure, school_label in ((a, 'a'), (b, 'b')):
            for index in range(1, 11):
                username = f'demo_student_{school_label}_{index:02d}'
                user = self._user(
                    username, role='student', school=structure['school'],
                    year=structure['years']['current'],
                )
                student, _ = Student.objects.update_or_create(
                    user=user,
                    defaults={
                        'school': structure['school'], 'full_name': f'DEMO Student {school_label.upper()} {index:02d}',
                        'gender': 'male' if index % 2 else 'female', 'is_active': True,
                    },
                )
                grade = 6 if index <= 6 else 7
                section_code = 'B' if school_label == 'b' and grade == 6 else 'A'
                enrollment, _ = StudentEnrollment.objects.update_or_create(
                    student=student, academic_year=structure['years']['current'],
                    defaults={
                        'school': structure['school'],
                        'classroom': structure['classrooms'][('current', grade)],
                        'section': structure['sections'][('current', grade, section_code)],
                        'status': 'active', 'is_current': True,
                    },
                )
                self._membership(user, structure['school'], 'student', default=True)
                students.append(student)
                enrollments.append(enrollment)

        transferred_user = self._user(
            'demo_student_transferred', role='student', school=school_b, year=year_b,
        )
        transferred, _ = Student.objects.update_or_create(
            user=transferred_user,
            defaults={'school': school_b, 'full_name': 'DEMO Transferred Student', 'gender': 'female'},
        )
        old_enrollment, _ = StudentEnrollment.objects.update_or_create(
            student=transferred, academic_year=a['years']['previous'],
            defaults={
                'school': school_a, 'classroom': a['classrooms'][('previous', 6)],
                'section': a['sections'][('previous', 6, 'A')],
                'status': 'transferred', 'is_current': False,
            },
        )
        current_enrollment, _ = StudentEnrollment.objects.update_or_create(
            student=transferred, academic_year=year_b,
            defaults={
                'school': school_b, 'classroom': b['classrooms'][('current', 6)],
                'section': b['sections'][('current', 6, 'B')],
                'status': 'active', 'is_current': True,
            },
        )
        transferred_old_m = self._membership(transferred_user, school_a, 'student', status='historical')
        transferred_current_m = self._membership(transferred_user, school_b, 'student', default=True)
        enrollments.extend((old_enrollment, current_enrollment))
        students.append(transferred)

        StudentGuardian.objects.update_or_create(
            parent=parents['demo_parent_a'], student=students[0],
            defaults={'relationship': 'father', 'is_primary': True, 'can_receive_notifications': True},
        )
        StudentGuardian.objects.update_or_create(
            parent=parents['demo_parent_a'], student=students[1],
            defaults={'relationship': 'father', 'can_receive_notifications': True},
        )
        StudentGuardian.objects.update_or_create(
            parent=parents['demo_parent_multi'], student=transferred,
            defaults={'relationship': 'guardian', 'is_primary': True, 'can_receive_notifications': True},
        )
        self._membership(
            parents['demo_parent_multi'].user, school_a, 'parent', status='historical',
        )

        for index, enrollment in enumerate(enrollments):
            structure = a if enrollment.school_id == school_a.pk else b
            term_key = 'previous' if enrollment.academic_year_id == structure['years']['previous'].pk else 'current'
            assignment = None
            if term_key == 'current':
                candidate = assignments['a_math'] if enrollment.school_id == school_a.pk else assignments['b_math']
                if candidate.classroom_id == enrollment.classroom_id and candidate.section_id == enrollment.section_id:
                    assignment = candidate
            Attendance.objects.update_or_create(
                student_enrollment=enrollment,
                attendance_date=structure['terms'][term_key].start_date + timedelta(days=10),
                defaults={
                    'teacher_assignment': assignment, 'academic_term': structure['terms'][term_key],
                    'status': ('present', 'absent', 'late', 'excused')[index % 4],
                    'note': 'DEMO attendance',
                },
            )

        # Student Attendance V1 acceptance data for demo_student_a_01.
        attendance_enrollment = StudentEnrollment.objects.get(
            student__user__username='demo_student_a_01', academic_year=year_a,
        )
        active_term_a = next(
            (t for t in (a['terms']['current'], a['terms']['current_2'], a['terms']['current_3']) if t.is_active),
            a['terms']['current'],
        )
        base_attendance_date = active_term_a.start_date + timedelta(days=1)
        attendance_specs = (
            (0, 'present', 'حضور منتظم.'),
            (1, 'present', ''),
            (2, 'late', 'تأخر عن بداية اليوم الدراسي.'),
            (3, 'present', ''),
            (4, 'absent', 'غياب بدون عذر مسجل.'),
            (7, 'present', ''),
            (8, 'excused', 'غياب بعذر معتمد من المدرسة.'),
            (9, 'present', ''),
            (10, 'late', 'تأخر بسيط.'),
            (11, 'present', ''),
            (14, 'present', ''),
            (15, 'present', ''),
            (16, 'present', ''),
            (17, 'absent', 'غياب بدون عذر مسجل.'),
            (18, 'present', ''),
        )
        for day_offset, attendance_status, attendance_note in attendance_specs:
            attendance_date = base_attendance_date + timedelta(days=day_offset)
            Attendance.objects.update_or_create(
                student_enrollment=attendance_enrollment,
                attendance_date=attendance_date,
                defaults={
                    'teacher_assignment': assignments['a_math'],
                    'academic_term': active_term_a,
                    'status': attendance_status,
                    'note': f'DEMO attendance V1 | {attendance_note}',
                },
            )

        active_term_b = next(
            (t for t in (b['terms']['current'], b['terms']['current_2'], b['terms']['current_3']) if t.is_active),
            b['terms']['current'],
        )
        hw_due_a = min(
            timezone.now() + timedelta(days=7),
            timezone.make_aware(datetime.combine(active_term_a.end_date, time.max)),
        )
        hw_due_b = min(
            timezone.now() + timedelta(days=7),
            timezone.make_aware(datetime.combine(active_term_b.end_date, time.max)),
        )
        homework, _ = Homework.objects.update_or_create(
            teacher_assignment=assignments['a_math'], title='DEMO Published Mathematics Homework',
            defaults={
                'school': school_a, 'academic_year': year_a, 'academic_term': active_term_a,
                'description': 'DEMO homework', 'submission_type': 'text', 'status': 'published',
                'published_at': timezone.now(), 'due_date': hw_due_a,
                'max_grade': Decimal('10'), 'created_by': teacher_a_user,
            },
        )
        Homework.objects.update_or_create(
            teacher_assignment=assignments['b_math'], title='DEMO School B Mathematics Homework',
            defaults={
                'school': school_b, 'academic_year': year_b, 'academic_term': active_term_b,
                'description': 'DEMO School B homework', 'submission_type': 'text_and_attachment', 'status': 'published',
                'published_at': timezone.now(), 'due_date': hw_due_b,
                'max_grade': Decimal('10'), 'created_by': multi_user,
            },
        )
        # Homework V1 submission-mode acceptance data for demo_student_a_01.
        # update_or_create keeps repeated demo seeding idempotent.
        homework_submission_modes = (
            (
                'DEMO Homework - Notebook Only', 'none',
                'حل التمارين من 1 إلى 5 في دفتر الرياضيات. لا يحتاج هذا الواجب إلى تسليم إلكتروني.',
            ),
            (
                'DEMO Homework - Text Answer', 'text',
                'اكتب في التطبيق شرحاً مختصراً لطريقة حل المسألة.',
            ),
            (
                'DEMO Homework - Attachment Only', 'attachment',
                'حل الواجب في الدفتر ثم ارفع صورة واضحة أو ملف PDF للحل.',
            ),
            (
                'DEMO Homework - Text And Attachment', 'text_and_attachment',
                'اكتب ملخص الحل ثم أرفق صورة أو PDF يوضح خطوات الحل كاملة.',
            ),
        )
        hw_due_modes = min(
            timezone.now() + timedelta(days=10),
            timezone.make_aware(datetime.combine(active_term_a.end_date, time.max)),
        )
        for demo_title, submission_type, description in homework_submission_modes:
            Homework.objects.update_or_create(
                teacher_assignment=assignments['a_math'], title=demo_title,
                defaults={
                    'school': school_a, 'academic_year': year_a,
                    'academic_term': active_term_a,
                    'description': description, 'submission_type': submission_type,
                    'status': 'published', 'published_at': timezone.now(),
                    'due_date': hw_due_modes,
                    'max_grade': None if submission_type == 'none' else Decimal('10'),
                    'created_by': teacher_a_user,
                },
            )

        eligible_a = [item for item in enrollments if item.school_id == school_a.pk and item.classroom_id == assignments['a_math'].classroom_id]
        if eligible_a:
            HomeworkSubmission.objects.update_or_create(
                homework=homework, student_enrollment=eligible_a[0],
                defaults={
                    'answer': 'DEMO submitted answer', 'status': 'graded',
                    'submitted_at': timezone.now(), 'grade': Decimal('9'),
                    'graded_by': teacher_a_user, 'graded_at': timezone.now(),
                },
            )

        # Results acceptance dataset. Keep all records deterministic and update-or-create so
        # repeated demo seeding never duplicates them. The first Grade 6/A School A
        # enrollment is demo_student_a_01.
        if eligible_a:
            result_student = StudentEnrollment.objects.get(
                student__user__username='demo_student_a_01', academic_year=year_a,
            )
            term_1_start = a['terms']['current'].start_date
            term_2_start = a['terms']['current_2'].start_date
            result_specs = (
                # title, exam type, assignment, term, date, max marks, score, remarks, published
                (
                    'DEMO Published Quiz', 'DEMO_QUIZ', assignments['a_math'],
                    a['terms']['current'], term_1_start + timedelta(days=44), '20', '18',
                    'DEMO quiz feedback: بداية ممتازة.', True,
                ),
                (
                    'DEMO Monthly Mathematics', 'DEMO_MONTHLY', assignments['a_math'],
                    a['terms']['current'], term_1_start + timedelta(days=51), '20', '18',
                    'استمر على هذا المستوى في الاختبارات الشهرية.', True,
                ),
                (
                    'DEMO Midterm Science', 'DEMO_MID', assignments['a_science_g6'],
                    a['terms']['current'], term_1_start + timedelta(days=65), '50', '42',
                    'فهم جيد للمفاهيم العلمية، راجع الأسئلة التطبيقية.', True,
                ),
                (
                    'DEMO Term Arabic', 'DEMO_TERM', assignments['a_arabic_g6'],
                    a['terms']['current'], term_1_start + timedelta(days=79), '30', '27',
                    'أداء متميز في القراءة والقواعد.', True,
                ),
                (
                    'DEMO Final Mathematics', 'DEMO_FINAL', assignments['a_math'],
                    a['terms']['current_2'], term_2_start + timedelta(days=73), '100', '86',
                    'نتيجة نهائية قوية مع فرصة لتحسين مسائل الهندسة.', True,
                ),
                (
                    'DEMO Unpublished Mathematics Result', 'DEMO_QUIZ', assignments['a_math'],
                    a['terms']['current_2'], term_2_start + timedelta(days=80), '20', '17',
                    'هذه النتيجة للاختبار فقط ويجب ألا تظهر للطالب.', False,
                ),
            )
            for (
                title, type_code, assignment, academic_term, exam_date, total, score, remarks, published
            ) in result_specs:
                exam_type = ExamType.objects.get(school=school_a, code=type_code)
                result_exam, _ = Exam.objects.update_or_create(
                    academic_term=academic_term,
                    teacher_assignment=assignment,
                    exam_type=exam_type,
                    title=title,
                    defaults={
                        'school': school_a, 'academic_year': year_a,
                        'created_by': teacher_a_user, 'exam_date': exam_date,
                        'total_marks': Decimal(total), 'status': 'published',
                    },
                )
                ExamResult.objects.update_or_create(
                    exam=result_exam, student_enrollment=result_student,
                    defaults={
                        'score': Decimal(score), 'status': 'present',
                        'workflow_status': 'approved', 'remarks': remarks,
                        'graded_by': teacher_a_user, 'approved_by': admin_a,
                        'is_published': published,
                        'published_at': timezone.now() if published else None,
                        'published_by': admin_a if published else None,
                    },
                )

        # Historical results acceptance uses the transferred demo student because it has
        # a real historical School A membership and a separate current School B context.
        historical_exam_type = ExamType.objects.get(school=school_a, code='DEMO_QUIZ')
        historical_exam, _ = Exam.objects.update_or_create(
            academic_term=a['terms']['previous'],
            teacher_assignment=assignments['a_math_previous'],
            exam_type=historical_exam_type,
            title='DEMO Historical Mathematics Quiz',
            defaults={
                'school': school_a, 'academic_year': a['years']['previous'],
                'created_by': teacher_a_user,
                'exam_date': a['terms']['previous'].start_date + timedelta(days=49),
                'total_marks': Decimal('20'), 'status': 'published',
            },
        )
        ExamResult.objects.update_or_create(
            exam=historical_exam, student_enrollment=old_enrollment,
            defaults={
                'score': Decimal('14'), 'status': 'present',
                'workflow_status': 'approved',
                'remarks': 'نتيجة تاريخية تجريبية للعرض فقط.',
                'graded_by': teacher_a_user, 'approved_by': admin_a,
                'is_published': True, 'published_at': timezone.now(),
                'published_by': admin_a,
            },
        )

        announcement, _ = Announcement.objects.update_or_create(
            school=school_a, title='DEMO School Announcement',
            defaults={
                'academic_year': year_a, 'body': 'DEMO school-wide announcement',
                'status': 'published', 'audience_type': 'school',
                'created_by_membership': SchoolMembership.objects.get(user=admin_a, school=school_a),
                'published_by_membership': SchoolMembership.objects.get(user=admin_a, school=school_a),
                'published_at': timezone.now(),
            },
        )
        for membership in SchoolMembership.objects.filter(school=school_a, status='active').exclude(role='super_admin'):
            AnnouncementReceipt.objects.get_or_create(
                announcement=announcement, recipient_membership=membership,
            )
        AnnouncementReceipt.objects.get_or_create(
            announcement=announcement, recipient_membership=transferred_old_m,
        )
        announcement_b, _ = Announcement.objects.update_or_create(
            school=school_b, title='DEMO School B Announcement',
            defaults={
                'academic_year': year_b, 'body': 'DEMO school B announcement',
                'status': 'published', 'audience_type': 'roles', 'target_roles': ['student'],
                'created_by_membership': SchoolMembership.objects.get(user=admin_b, school=school_b),
                'published_by_membership': SchoolMembership.objects.get(user=admin_b, school=school_b),
                'published_at': timezone.now(),
            },
        )
        for membership in SchoolMembership.objects.filter(
            school=school_b, role='student', status='active',
        ):
            AnnouncementReceipt.objects.get_or_create(
                announcement=announcement_b, recipient_membership=membership,
            )
        demo_student_a01 = Student.objects.get(user__username='demo_student_a_01')
        demo_student_a01_m = SchoolMembership.objects.get(
            user=demo_student_a01.user, school=school_a, role='student', status='active',
        )
        Notification.objects.update_or_create(
            recipient_membership=demo_student_a01_m, deduplication_key='DEMO:student:a01:announcement',
            defaults={
                'school': school_a, 'recipient': demo_student_a01.user,
                'notification_type': 'announcement_published',
                'title': 'موعد الاختبارات النهائية',
                'body': 'تم نشر إعلان جديد من المدرسة.',
                'source_type': 'announcement', 'source_id': announcement.pk,
                'payload': {'action': {'route': 'announcement_detail', 'params': {'announcement_id': announcement.pk}}},
            },
        )
        demo_result_for_notification = ExamResult.objects.get(
            exam__title='DEMO Final Mathematics',
            student_enrollment__student=demo_student_a01,
            is_published=True,
        )
        Notification.objects.update_or_create(
            recipient_membership=demo_student_a01_m, deduplication_key='DEMO:student:a01:result',
            defaults={
                'school': school_a, 'recipient': demo_student_a01.user,
                'notification_type': 'result_published',
                'title': 'تم نشر نتيجة جديدة', 'body': 'يمكنك مراجعة النتيجة من التطبيق.',
                'source_type': 'exam_result', 'source_id': demo_result_for_notification.pk,
                'payload': {'action': {'route': 'result_detail', 'params': {'result_id': demo_result_for_notification.pk}}},
            },
        )
        student_chat, _ = Conversation.objects.update_or_create(
            school=school_a, conversation_type='teacher_student', subject='مناقشة الواجب - تمارين المعادلات',
            defaults={'created_by_membership': teacher_a_m, 'status': 'open', 'priority': 'normal'},
        )
        for member, role in ((teacher_a_m, 'teacher'), (demo_student_a01_m, 'student')):
            ConversationParticipant.objects.update_or_create(
                conversation=student_chat, membership=member,
                defaults={'participant_role': role, 'can_reply': True, 'is_active': True},
            )
        Message.objects.update_or_create(
            conversation=student_chat, sender_membership=teacher_a_m,
            body='بخصوص واجب تمارين المعادلات، إذا احتجت توضيحاً اكتب هنا.',
            defaults={'message_type': 'text'},
        )
        student_support, _ = Conversation.objects.update_or_create(
            school=school_a, conversation_type='school_support', subject='استفسار عن بيانات الطالب',
            defaults={'created_by_membership': demo_student_a01_m, 'status': 'in_progress', 'category': 'profile_update', 'priority': 'normal'},
        )
        for member, role in ((demo_student_a01_m, 'student'), (SchoolMembership.objects.get(user=admin_a, school=school_a), 'school_admin')):
            ConversationParticipant.objects.update_or_create(
                conversation=student_support, membership=member,
                defaults={'participant_role': role, 'can_reply': True, 'is_active': True},
            )
        Message.objects.update_or_create(
            conversation=student_support, sender_membership=demo_student_a01_m,
            body='أرغب في مراجعة بيانات الطالب.', defaults={'message_type': 'text'},
        )

        Notification.objects.update_or_create(
            recipient_membership=teacher_a_m, deduplication_key='DEMO:system:welcome',
            defaults={
                'school': school_a, 'recipient': teacher_a_user, 'notification_type': 'system',
                'title': 'DEMO Welcome', 'body': 'DEMO notification',
                'source_type': 'demo', 'source_id': announcement.pk,
            },
        )
        Notification.objects.update_or_create(
            recipient_membership=transferred_current_m, deduplication_key='DEMO:transfer:current',
            defaults={
                'school': school_b, 'recipient': transferred_user, 'notification_type': 'system',
                'title': 'DEMO Current School', 'body': 'DEMO current membership notification',
                'source_type': 'demo', 'source_id': current_enrollment.pk,
            },
        )
        # Release 1.0 admin acceptance data: richer operational records for
        # timetable, attendance, homework, communications and reports.
        for index, enrollment in enumerate(
            StudentEnrollment.objects.filter(
                school=school_a, academic_year=year_a, classroom=assignments['a_math'].classroom,
                section=assignments['a_math'].section, status='active', is_current=True,
            ).select_related('student')[:6],
            start=1,
        ):
            for offset, attendance_status in ((2, 'present'), (3, 'late'), (4, 'absent')):
                attendance_day = active_term_a.start_date + timedelta(days=20 + offset)
                Attendance.objects.update_or_create(
                    student_enrollment=enrollment, attendance_date=attendance_day,
                    defaults={
                        'teacher_assignment': assignments['a_math'],
                        'academic_term': active_term_a, 'status': attendance_status,
                        'note': f'DEMO Release 1 attendance {index}',
                    },
                )

        demo_admin_homework, _ = Homework.objects.update_or_create(
            teacher_assignment=assignments['a_math'],
            title='DEMO Release 1 - واجب مراجعة الرياضيات',
            defaults={
                'school': school_a, 'academic_year': year_a, 'academic_term': active_term_a,
                'description': 'بيانات تجريبية لفحص إدارة الواجبات والتقارير.',
                'submission_type': 'text_and_attachment', 'status': 'published',
                'published_at': timezone.now(), 'due_date': hw_due_a,
                'max_grade': Decimal('10'), 'created_by': teacher_a_user,
            },
        )
        for index, enrollment in enumerate(eligible_a[:4], start=1):
            HomeworkSubmission.objects.update_or_create(
                homework=demo_admin_homework, student_enrollment=enrollment,
                defaults={
                    'answer': f'DEMO Release 1 submission {index}',
                    'status': 'graded' if index <= 2 else 'submitted',
                    'submitted_at': timezone.now(),
                    'grade': Decimal('9') if index <= 2 else None,
                    'graded_by': teacher_a_user if index <= 2 else None,
                    'graded_at': timezone.now() if index <= 2 else None,
                },
            )

        for title, audience, body in (
            ('DEMO Release 1 - تنبيه الاختبارات', 'school', 'تذكير تجريبي بموعد الاختبارات القادمة.'),
            ('DEMO Release 1 - نشاط طلابي', 'roles', 'إعلان تجريبي لاختبار شاشة الاتصالات.'),
        ):
            release_announcement, _ = Announcement.objects.update_or_create(
                school=school_a, title=title,
                defaults={
                    'academic_year': year_a, 'body': body, 'status': 'published',
                    'audience_type': audience,
                    'target_roles': ['student', 'parent'] if audience == 'roles' else [],
                    'created_by_membership': SchoolMembership.objects.get(user=admin_a, school=school_a),
                    'published_by_membership': SchoolMembership.objects.get(user=admin_a, school=school_a),
                    'published_at': timezone.now(),
                },
            )
            for membership in SchoolMembership.objects.filter(
                school=school_a, status='active',
            ).exclude(role='super_admin'):
                AnnouncementReceipt.objects.get_or_create(
                    announcement=release_announcement, recipient_membership=membership,
                )

        support, _ = Conversation.objects.update_or_create(
            school=school_a, conversation_type='school_support',
            subject='DEMO Academic Support',
            defaults={
                'created_by_membership': teacher_a_m, 'status': 'open',
                'category': 'academic_inquiry', 'priority': 'normal',
            },
        )
        ConversationParticipant.objects.update_or_create(
            conversation=support, membership=teacher_a_m,
            defaults={'participant_role': 'teacher', 'can_reply': True, 'is_active': True},
        )
        Message.objects.update_or_create(
            conversation=support, sender_membership=teacher_a_m,
            body='DEMO support message',
            defaults={'message_type': 'text'},
        )
        return {
            'schools': School.objects.filter(code__in=DEMO_SCHOOL_CODES).count(),
            'students': Student.objects.filter(user__username__startswith='demo_').count(),
            'attendance': Attendance.objects.filter(note__startswith='DEMO attendance').count(),
            'published_results': ExamResult.objects.filter(
                exam__school__code__in=DEMO_SCHOOL_CODES, is_published=True,
            ).count(),
            'super_admin': super_admin.pk, 'multi_membership': multi_a.pk,
        }
