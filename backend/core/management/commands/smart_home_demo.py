from datetime import datetime, time, timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from core.models import (
    AcademicTerm,
    Announcement,
    AnnouncementReceipt,
    Attendance,
    Exam,
    ExamResult,
    ExamType,
    Homework,
    HomeworkActionLog,
    Notification,
    SchoolMembership,
    SchoolPeriod,
    SchoolTimetableConfig,
    StudentEnrollment,
    Subject,
    Teacher,
    TeacherAssignment,
    TimetableEntry,
    User,
)


PREFIX = "SMART_HOME_DEMO_"
USERNAME = "demo_student_a_01"
HOMEWORK_TITLES = {
    "OVERDUE": "حل تمارين الرياضيات المتأخرة",
    "DUE_TODAY": "مراجعة درس العلوم لليوم",
    "UPCOMING": "كتابة ملخص درس اللغة العربية",
    "OLDER_NON_URGENT": "قراءة الفصل القادم من الكتاب",
}
RESULT_TITLES = {
    False: "نتيجة الرياضيات التجريبية",
    True: "نتيجة الرياضيات للفصل السابق",
}
ANNOUNCEMENT_TITLES = {
    False: "تنبيه دراسي للطلاب",
    True: "إعلان نهاية الفصل الدراسي",
}


class Command(BaseCommand):
    help = "Prepare repeatable Smart Student Home demo data."

    def add_arguments(self, parser):
        parser.add_argument(
            "mode",
            choices=("busy", "calm", "historical", "status"),
            help="Demo scenario to prepare or inspect.",
        )

    def handle(self, *args, **options):
        context = self._resolve()
        mode = options["mode"]
        if mode == "status":
            self._print_status(context)
            return
        with transaction.atomic():
            if mode in ("busy", "calm"):
                self._prepare_current(context, busy=mode == "busy")
            else:
                self._prepare_historical(context)
        self.stdout.write(self.style.SUCCESS(f"Smart Home demo mode ready: {mode}"))
        self._print_status(context)

    def _resolve(self):
        try:
            user = User.objects.select_related("student_profile").get(
                username=USERNAME
            )
        except User.DoesNotExist as exc:
            raise CommandError(f"Required demo user {USERNAME!r} was not found.") from exc
        student = user.student_profile
        current = (
            StudentEnrollment.objects.select_related(
                "school", "academic_year", "classroom", "section"
            )
            .filter(student=student, is_current=True, status="active")
            .first()
        )
        historical = (
            StudentEnrollment.objects.select_related(
                "school", "academic_year", "classroom", "section"
            )
            .filter(student=student, is_current=False)
            .exclude(status="active")
            .order_by("-academic_year__end_date", "-pk")
            .first()
        )
        if current is None or historical is None:
            raise CommandError("The accepted current and historical enrollments are required.")
        current_membership = SchoolMembership.objects.filter(
            user=user,
            school=current.school,
            role="student",
            status="active",
        ).first()
        historical_membership = SchoolMembership.objects.filter(
            user=user,
            school=historical.school,
            role="student",
            status="historical",
        ).first()
        if current_membership is None or historical_membership is None:
            raise CommandError("The accepted student memberships could not be resolved.")
        return {
            "user": user,
            "student": student,
            "current": current,
            "historical": historical,
            "current_membership": current_membership,
            "historical_membership": historical_membership,
        }

    def _admin(self, enrollment):
        membership = (
            SchoolMembership.objects.select_related("user")
            .filter(
                school=enrollment.school,
                role="school_admin",
                status="active",
                user__school=enrollment.school,
            )
            .first()
        )
        if membership is None:
            raise CommandError(
                f"An active school administrator is required for {enrollment.school}."
            )
        return membership

    def _term(self, enrollment):
        local_date = timezone.localdate()
        term = AcademicTerm.objects.filter(
            school=enrollment.school,
            academic_year=enrollment.academic_year,
            start_date__lte=local_date,
            end_date__gte=local_date,
        ).first()
        if term is None:
            term = AcademicTerm.objects.filter(
                school=enrollment.school,
                academic_year=enrollment.academic_year,
            ).order_by("-end_date").first()
        if term is None:
            raise CommandError(f"No academic term exists for {enrollment.academic_year}.")
        return term

    def _assignment(self, enrollment):
        assignment = TeacherAssignment.objects.filter(
            school=enrollment.school,
            academic_year=enrollment.academic_year,
            classroom=enrollment.classroom,
            section=enrollment.section,
            is_current=True,
        ).select_related("subject").first()
        if assignment:
            return assignment
        subject, _ = Subject.objects.get_or_create(
            school=enrollment.school,
            code=f"{PREFIX}SUBJECT",
            defaults={"name": "الرياضيات التجريبية", "is_active": True},
        )
        teacher = Teacher.objects.filter(
            school=enrollment.school,
            academic_year=enrollment.academic_year,
            full_name=f"{PREFIX}TEACHER",
        ).first()
        if teacher is None:
            teacher = Teacher.objects.create(
                school=enrollment.school,
                academic_year=enrollment.academic_year,
                full_name=f"{PREFIX}TEACHER",
                specialization="Demo data",
            )
        assignment, _ = TeacherAssignment.objects.get_or_create(
            teacher=teacher,
            school=enrollment.school,
            academic_year=enrollment.academic_year,
            classroom=enrollment.classroom,
            section=enrollment.section,
            subject=subject,
            defaults={"is_current": True},
        )
        if not assignment.is_current:
            assignment.is_current = True
            assignment.save(update_fields=("is_current",))
        return assignment

    def _tracked_item(self, model, school, entity_type, key, legacy_query):
        marker = HomeworkActionLog.objects.filter(
            school=school,
            entity_type=entity_type,
            action=key,
        ).order_by("-pk").first()
        item = (
            model.objects.filter(pk=marker.entity_id, school=school).first()
            if marker
            else None
        )
        return item or legacy_query.order_by("-pk").first()

    def _track_item(self, item, entity_type, key):
        marker = HomeworkActionLog.objects.filter(
            school=item.school,
            entity_type=entity_type,
            action=key,
        ).order_by("-pk").first()
        if marker is None:
            HomeworkActionLog.objects.create(
                school=item.school,
                action=key,
                entity_type=entity_type,
                entity_id=item.pk,
                reason=f"{PREFIX}{key}",
            )
        elif marker.entity_id != item.pk:
            marker.entity_id = item.pk
            marker.reason = f"{PREFIX}{key}"
            marker.save(update_fields=("entity_id", "reason"))

    def _homework(self, enrollment, assignment, term, key, due_at, published_at):
        item = self._tracked_item(
            Homework,
            enrollment.school,
            "smart_home_demo_homework",
            key,
            Homework.objects.filter(
                school=enrollment.school,
                academic_year=enrollment.academic_year,
                teacher_assignment=assignment,
                title=f"{PREFIX}{key}",
            ),
        )
        values = {
            "academic_term": term,
            "description": "تدريب تجريبي لاختبار الصفحة الرئيسية الذكية.",
            "submission_type": "text",
            "status": "published",
            "published_at": published_at,
            "publish_at": None,
            "due_date": due_at,
            "max_grade": Decimal("10.00"),
        }
        if item is None:
            item = Homework(
                school=enrollment.school,
                academic_year=enrollment.academic_year,
                teacher_assignment=assignment,
                title=HOMEWORK_TITLES[key],
                **values,
            )
        else:
            item.title = HOMEWORK_TITLES[key]
            for field, value in values.items():
                setattr(item, field, value)
        item.save()
        self._track_item(item, "smart_home_demo_homework", key)
        return item

    def _prepare_current(self, context, *, busy):
        enrollment = context["current"]
        membership = context["current_membership"]
        admin = self._admin(enrollment)
        assignment = self._assignment(enrollment)
        term = self._term(enrollment)
        now = timezone.now()
        local_now = timezone.localtime(now)
        published = now - timedelta(days=7)
        due_dates = (
            (
                now - timedelta(days=1),
                now.replace(hour=23, minute=59, second=0, microsecond=0),
                now + timedelta(days=2),
            )
            if busy
            else (now + timedelta(days=4), now + timedelta(days=5), now + timedelta(days=2))
        )
        self._homework(enrollment, assignment, term, "OVERDUE", due_dates[0], published)
        self._homework(enrollment, assignment, term, "DUE_TODAY", due_dates[1], published)
        self._homework(enrollment, assignment, term, "UPCOMING", due_dates[2], published)
        self._homework(
            enrollment,
            assignment,
            term,
            "OLDER_NON_URGENT",
            now + timedelta(days=8),
            published - timedelta(days=10),
        )
        self._prepare_timetable(enrollment, assignment, local_now, dynamic=busy)
        self._prepare_attendance(enrollment, assignment, term, historical=False)
        self._prepare_result(enrollment, assignment, term, admin, historical=False)
        self._prepare_announcement(enrollment, membership, admin, historical=False)
        notification, _ = Notification.objects.update_or_create(
            recipient_membership=membership,
            deduplication_key=f"{PREFIX}CURRENT_NOTIFICATION",
            defaults={
                "school": enrollment.school,
                "recipient": context["user"],
                "notification_type": "system",
                "title": "تحديث دراسي جديد",
                "body": "لديك تحديث تجريبي لاختبار الصفحة الرئيسية الذكية.",
                "payload": {"action": {"route": "school_home", "params": {}}},
                "source_type": "smart_home_demo",
                "is_read": not busy,
                "read_at": None if busy else now,
            },
        )
        notification.full_clean()
        notification.save()

    def _prepare_historical(self, context):
        enrollment = context["historical"]
        membership = context["historical_membership"]
        admin = self._admin(enrollment)
        assignment = self._assignment(enrollment)
        term = self._term(enrollment)
        historical_date = min(term.end_date, enrollment.academic_year.end_date)
        aware = timezone.make_aware(datetime.combine(historical_date, time(12, 0)))
        self._prepare_timetable(enrollment, assignment, timezone.localtime(aware), dynamic=False)
        self._prepare_attendance(enrollment, assignment, term, historical=True)
        self._prepare_result(enrollment, assignment, term, admin, historical=True)
        self._prepare_announcement(enrollment, membership, admin, historical=True)

    def _prepare_timetable(self, enrollment, assignment, local_now, *, dynamic):
        marker = f"{PREFIX}{enrollment.academic_year_id}_"
        periods = SchoolPeriod.objects.filter(
            school=enrollment.school,
            academic_year=enrollment.academic_year,
            name__startswith=marker,
        )
        TimetableEntry.objects.filter(period__in=periods).delete()
        periods.delete()
        weekday = (timezone.localdate().weekday() + 1) % 7
        config, _ = SchoolTimetableConfig.objects.get_or_create(
            school=enrollment.school,
            academic_year=enrollment.academic_year,
            defaults={"working_days": [weekday]},
        )
        if weekday not in config.working_days:
            config.working_days = [*config.working_days, weekday]
            config.save(update_fields=("working_days", "updated_at"))
        if dynamic and local_now.time() < time(23, 35):
            current_start = local_now - timedelta(minutes=10)
            current_end = local_now + timedelta(minutes=15)
            next_start = local_now + timedelta(minutes=20)
            next_end = local_now + timedelta(minutes=50)
        else:
            current_start = datetime.combine(local_now.date(), time(5, 0), local_now.tzinfo)
            current_end = current_start + timedelta(minutes=40)
            next_start = current_end + timedelta(minutes=10)
            next_end = next_start + timedelta(minutes=40)
        rows = (
            (90, "CURRENT", current_start.time(), current_end.time()),
            (91, "NEXT", next_start.time(), next_end.time()),
        )
        for sequence, label, start, end in rows:
            period = SchoolPeriod.objects.create(
                school=enrollment.school,
                academic_year=enrollment.academic_year,
                name=f"{marker}{label}",
                sequence=sequence,
                start_time=start.replace(second=0, microsecond=0),
                end_time=end.replace(second=0, microsecond=0),
                kind="lesson",
            )
            TimetableEntry.objects.create(
                school=enrollment.school,
                academic_year=enrollment.academic_year,
                teacher_assignment=assignment,
                weekday=weekday,
                period=period,
                room_or_location="قاعة العرض التجريبية",
                is_active=True,
            )

    def _prepare_attendance(self, enrollment, assignment, term, *, historical):
        base = term.end_date - timedelta(days=10) if historical else timezone.localdate() - timedelta(days=9)
        statuses = ("present", "present", "present", "present", "present", "present", "present", "late", "absent", "present")
        for offset, status in enumerate(statuses):
            date = base + timedelta(days=offset)
            if not (term.start_date <= date <= term.end_date):
                continue
            Attendance.objects.update_or_create(
                student_enrollment=enrollment,
                attendance_date=date,
                defaults={
                    "teacher_assignment": assignment,
                    "academic_term": term,
                    "status": status,
                    "note": f"{PREFIX}ATTENDANCE",
                },
            )

    def _prepare_result(self, enrollment, assignment, term, admin, *, historical):
        exam_type, _ = ExamType.objects.get_or_create(
            school=enrollment.school,
            code=f"{PREFIX}QUIZ",
            defaults={"name": "اختبار قصير تجريبي", "max_score": 20, "weight_percentage": 10},
        )
        exam_date = term.end_date - timedelta(days=5) if historical else min(timezone.localdate() - timedelta(days=2), term.end_date)
        key = "HISTORICAL_RESULT" if historical else "RECENT_RESULT"
        exam = self._tracked_item(
            Exam,
            enrollment.school,
            "smart_home_demo_exam",
            key,
            Exam.objects.filter(
                academic_term=term,
                teacher_assignment=assignment,
                exam_type=exam_type,
                title=f"{PREFIX}{key}",
            ),
        )
        if exam is None:
            exam = Exam(
                school=enrollment.school,
                academic_year=enrollment.academic_year,
                academic_term=term,
                teacher_assignment=assignment,
                exam_type=exam_type,
                title=RESULT_TITLES[historical],
            )
        exam.title = RESULT_TITLES[historical]
        exam.created_by = admin.user
        exam.exam_date = exam_date
        exam.total_marks = Decimal("20.00")
        exam.status = "published"
        exam.save()
        self._track_item(exam, "smart_home_demo_exam", key)
        now = timezone.now()
        ExamResult.objects.update_or_create(
            exam=exam,
            student_enrollment=enrollment,
            defaults={
                "score": Decimal("18.00") if not historical else Decimal("17.00"),
                "status": "present",
                "workflow_status": "approved",
                "is_published": True,
                "published_at": now - timedelta(days=1),
                "published_by": admin.user,
                "graded_by": admin.user,
                "approved_by": admin.user,
                "remarks": "أداء جيد",
            },
        )

    def _prepare_announcement(self, enrollment, membership, admin, *, historical):
        key = "HISTORICAL_ANNOUNCEMENT" if historical else "CURRENT_ANNOUNCEMENT"
        announcement = self._tracked_item(
            Announcement,
            enrollment.school,
            "smart_home_demo_announcement",
            key,
            Announcement.objects.filter(
                school=enrollment.school,
                title=f"{PREFIX}{key}",
            ),
        )
        if announcement is None:
            announcement = Announcement(
                school=enrollment.school,
                title=ANNOUNCEMENT_TITLES[historical],
            )
        announcement.title = ANNOUNCEMENT_TITLES[historical]
        announcement.academic_year = enrollment.academic_year
        announcement.body = "إعلان مدرسي تجريبي لاختبار آخر التحديثات."
        announcement.status = "published"
        announcement.priority = "normal"
        announcement.audience_type = "students"
        announcement.allow_inquiry = not historical
        announcement.created_by_membership = admin
        announcement.published_by_membership = admin
        announcement.published_at = timezone.now() - timedelta(hours=2)
        announcement.closed_at = None
        announcement.archived_at = None
        announcement.save()
        self._track_item(announcement, "smart_home_demo_announcement", key)
        announcement.target_students.set([enrollment.student])
        AnnouncementReceipt.objects.update_or_create(
            announcement=announcement,
            recipient_membership=membership,
            defaults={"read_at": timezone.now() if historical else None},
        )

    def _print_status(self, context):
        for label, key, membership_key in (
            ("Current", "current", "current_membership"),
            ("Historical", "historical", "historical_membership"),
        ):
            enrollment = context[key]
            membership = context[membership_key]
            self.stdout.write(
                f"{label}: membership={membership.pk} school={enrollment.school.name} "
                f"year={enrollment.academic_year.name} enrollment={enrollment.pk}"
            )
            self.stdout.write(
                "  Homework={homework} Timetable={timetable} Attendance={attendance} "
                "Results={results} Notifications={notifications} Announcements={announcements}".format(
                    homework=HomeworkActionLog.objects.filter(
                        school=enrollment.school,
                        entity_type="smart_home_demo_homework",
                    ).values("entity_id").distinct().count(),
                    timetable=TimetableEntry.objects.filter(
                        school=enrollment.school,
                        academic_year=enrollment.academic_year,
                        period__name__startswith=PREFIX,
                    ).count(),
                    attendance=Attendance.objects.filter(
                        student_enrollment=enrollment,
                        note=PREFIX + "ATTENDANCE",
                    ).count(),
                    results=HomeworkActionLog.objects.filter(
                        school=enrollment.school,
                        entity_type="smart_home_demo_exam",
                    ).values("entity_id").distinct().count(),
                    notifications=Notification.objects.filter(
                        recipient_membership=membership,
                        deduplication_key__startswith=PREFIX,
                    ).count(),
                    announcements=HomeworkActionLog.objects.filter(
                        school=enrollment.school,
                        entity_type="smart_home_demo_announcement",
                    ).values("entity_id").distinct().count(),
                )
            )
