from datetime import datetime
from io import StringIO
from unittest.mock import patch

from django.core.management import call_command
from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient

from .management.commands.seed_demo_school import DEMO_PASSWORD
from .models import (
    AcademicTerm, Attendance, SchoolMembership, SchoolPeriod, StudentEnrollment,
    TimetableEntry,
)


@override_settings(DEBUG=True)
class TimetableAPITests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command('seed_demo_school', stdout=StringIO())

    def setUp(self):
        self.client = APIClient()

    def login(self, username, school_code=None):
        response = self.client.post(
            '/api/v1/auth/login/', {'username': username, 'password': DEMO_PASSWORD}, format='json',
        )
        self.assertEqual(response.status_code, 200, response.data)
        credentials = {'HTTP_AUTHORIZATION': f"Bearer {response.data['access']}"}
        if school_code:
            membership = SchoolMembership.objects.get(
                user__username=username, school__code=school_code,
            )
            credentials['HTTP_X_SCHOOL_MEMBERSHIP_ID'] = str(membership.pk)
        self.client.credentials(**credentials)

    def test_multi_school_teacher_schedule_isolated_and_foreign_entry_404(self):
        self.login('demo_teacher_multi')
        self.assertEqual(self.client.get('/api/v1/timetable/week/').status_code, 409)
        self.login('demo_teacher_multi', 'DEMO_NOOR')
        a = self.client.get('/api/v1/timetable/week/')
        self.assertEqual(a.status_code, 200, a.data)
        ids_a = {entry['id'] for day in a.data['days'] for entry in day['entries']}
        foreign = TimetableEntry.objects.filter(school__code='DEMO_FUTURE').first()
        self.assertTrue(ids_a)
        self.assertEqual(self.client.get(f'/api/v1/timetable/entries/{foreign.pk}/').status_code, 404)
        self.login('demo_teacher_multi', 'DEMO_FUTURE')
        b = self.client.get('/api/v1/timetable/week/')
        ids_b = {entry['id'] for day in b.data['days'] for entry in day['entries']}
        self.assertTrue(ids_b)
        self.assertTrue(ids_a.isdisjoint(ids_b))

    def test_teacher_cannot_write_and_admin_grid_is_single_request(self):
        self.login('demo_teacher_a', 'DEMO_NOOR')
        period = SchoolPeriod.objects.filter(school__code='DEMO_NOOR', kind='lesson').first()
        response = self.client.post('/api/v1/timetable/entries/', {
            'teacher_assignment_id': period.timetable_entries.first().teacher_assignment_id,
            'period_id': period.pk, 'weekday': 2,
        }, format='json')
        self.assertEqual(response.status_code, 403)
        self.login('demo_school_a_admin', 'DEMO_NOOR')
        entry = TimetableEntry.objects.filter(school__code='DEMO_NOOR').first()
        grid = self.client.get('/api/v1/timetable/grid/', {
            'classroom_id': entry.teacher_assignment.classroom_id,
            'section_id': entry.teacher_assignment.section_id,
        })
        self.assertEqual(grid.status_code, 200, grid.data)
        self.assertIn('days', grid.data)
        self.assertIn('periods', grid.data)
        self.assertIn('entries', grid.data)

    def test_validate_only_does_not_write_and_bulk_is_atomic_on_conflict(self):
        self.login('demo_school_a_admin', 'DEMO_NOOR')
        entry = TimetableEntry.objects.filter(school__code='DEMO_NOOR').first()
        before = TimetableEntry.objects.count()
        cell = {
            'teacher_assignment_id': entry.teacher_assignment_id,
            'period_id': entry.period_id, 'weekday': 4,
        }
        preview = self.client.post('/api/v1/timetable/validate/', {'cells': [cell]}, format='json')
        self.assertEqual(preview.status_code, 200, preview.data)
        self.assertTrue(preview.data['valid'])
        self.assertEqual(TimetableEntry.objects.count(), before)
        conflict = self.client.post(
            '/api/v1/timetable/bulk/', {'cells': [cell, cell]}, format='json',
        )
        self.assertEqual(conflict.status_code, 400)
        self.assertEqual(TimetableEntry.objects.count(), before)

    def test_copy_day_clear_and_foreign_period_are_scoped(self):
        self.login('demo_school_a_admin', 'DEMO_NOOR')
        source = TimetableEntry.objects.filter(
            school__code='DEMO_NOOR', teacher_assignment__classroom__name='DEMO Grade 6',
            weekday=0,
        ).first()
        copied = self.client.post('/api/v1/timetable/copy-day/', {
            'source_classroom_id': source.teacher_assignment.classroom_id,
            'source_section_id': source.teacher_assignment.section_id,
            'source_weekday': 0, 'target_weekday': 2,
        }, format='json')
        self.assertEqual(copied.status_code, 200, copied.data)
        copied_id = copied.data['entries'][0]['id']
        cleared = self.client.post('/api/v1/timetable/bulk/', {
            'cells': [{'id': copied_id, 'action': 'clear'}],
        }, format='json')
        self.assertEqual(cleared.status_code, 200, cleared.data)
        self.assertFalse(TimetableEntry.objects.filter(pk=copied_id).exists())

        foreign_period = SchoolPeriod.objects.filter(school__code='DEMO_FUTURE').first()
        response = self.client.post('/api/v1/timetable/entries/', {
            'teacher_assignment_id': source.teacher_assignment_id,
            'period_id': foreign_period.pk, 'weekday': 3,
        }, format='json')
        self.assertEqual(response.status_code, 404)

    def test_break_is_in_timeline_but_not_an_entry(self):
        self.login('demo_teacher_multi', 'DEMO_NOOR')
        response = self.client.get('/api/v1/timetable/today/', {'date': '2026-08-09'})
        self.assertEqual(response.status_code, 200, response.data)
        self.assertTrue(any(period['kind'] == 'break' for period in response.data['periods']))
        self.assertTrue(all(entry['period_detail']['kind'] == 'lesson' for entry in response.data['entries']))

    def test_admin_config_period_and_entry_crud(self):
        self.login('demo_school_a_admin', 'DEMO_NOOR')
        config = self.client.get('/api/v1/timetable/config/')
        self.assertEqual(config.status_code, 200, config.data)
        updated = self.client.put(
            '/api/v1/timetable/config/', {'working_days': [0, 1, 2, 3, 4]}, format='json',
        )
        self.assertEqual(updated.status_code, 200, updated.data)
        periods = self.client.get('/api/v1/timetable/periods/')
        self.assertEqual(periods.status_code, 200, periods.data)

        existing = TimetableEntry.objects.filter(school__code='DEMO_NOOR').first()
        created_period = self.client.post('/api/v1/timetable/periods/', {
            'name': 'DEMO Fourth Lesson', 'sequence': 5,
            'start_time': '09:45:00', 'end_time': '10:30:00',
            'kind': 'lesson', 'is_active': True,
        }, format='json')
        self.assertEqual(created_period.status_code, 201, created_period.data)
        period_id = created_period.data['id']
        created = self.client.post('/api/v1/timetable/entries/', {
            'teacher_assignment_id': existing.teacher_assignment_id,
            'period_id': period_id, 'weekday': 3,
            'room_or_location': 'Updated Lab',
        }, format='json')
        self.assertEqual(created.status_code, 201, created.data)
        entry_id = created.data['id']
        detail = self.client.get(f'/api/v1/timetable/entries/{entry_id}/')
        self.assertEqual(detail.status_code, 200, detail.data)
        changed = self.client.put(f'/api/v1/timetable/entries/{entry_id}/', {
            'teacher_assignment_id': existing.teacher_assignment_id,
            'period_id': period_id, 'weekday': 4,
            'room_or_location': 'Room 44',
        }, format='json')
        self.assertEqual(changed.status_code, 200, changed.data)
        self.assertEqual(changed.data['room_or_location'], 'Room 44')
        protected = self.client.delete(f'/api/v1/timetable/periods/{period_id}/')
        self.assertEqual(protected.status_code, 400, protected.data)
        self.assertEqual(self.client.delete(f'/api/v1/timetable/entries/{entry_id}/').status_code, 204)
        self.assertEqual(self.client.delete(f'/api/v1/timetable/periods/{period_id}/').status_code, 204)

    def test_assignment_options_filters_and_copy_week_preview(self):
        self.login('demo_school_a_admin', 'DEMO_NOOR')
        entry = TimetableEntry.objects.filter(school__code='DEMO_NOOR').first()
        options = self.client.get('/api/v1/timetable/assignment-options/', {
            'classroom_id': entry.teacher_assignment.classroom_id,
            'section_id': entry.teacher_assignment.section_id,
        })
        self.assertEqual(options.status_code, 200, options.data)
        self.assertTrue(options.data)
        preview = self.client.post('/api/v1/timetable/copy-week/', {
            'source_classroom_id': entry.teacher_assignment.classroom_id,
            'source_section_id': entry.teacher_assignment.section_id,
            'target_classroom_id': entry.teacher_assignment.classroom_id,
            'target_section_id': entry.teacher_assignment.section_id,
            'validate_only': True,
        }, format='json')
        self.assertEqual(preview.status_code, 200, preview.data)
        self.assertFalse(preview.data['valid'])

        filtered = self.client.get('/api/v1/timetable/entries/', {
            'weekday': entry.weekday, 'teacher_assignment': entry.teacher_assignment_id,
            'subject': entry.teacher_assignment.subject_id, 'period': entry.period_id,
            'is_active': 'true', 'date': '2026-08-09',
        })
        self.assertEqual(filtered.status_code, 200, filtered.data)

    def test_current_and_next_are_deterministic_before_during_break_and_after(self):
        self.login('demo_teacher_multi', 'DEMO_NOOR')
        values = (
            (datetime(2026, 8, 9, 6, 30), False, 'DEMO Second Lesson'),
            (datetime(2026, 8, 9, 8, 0), True, 'DEMO First Lesson'),
            (datetime(2026, 8, 9, 8, 40), False, 'DEMO First Lesson'),
            (datetime(2026, 8, 9, 10, 0), False, 'DEMO First Lesson'),
        )
        for raw, has_current, next_name in values:
            moment = timezone.make_aware(raw)
            with patch('core.timetable_views.timezone.localtime', return_value=moment):
                current = self.client.get('/api/v1/timetable/current/')
                following = self.client.get('/api/v1/timetable/next/')
            self.assertEqual(bool(current.data['current_entry']), has_current)
            if next_name:
                self.assertEqual(following.data['next_entry']['period_detail']['name'], next_name)

    def test_student_parent_and_historical_access(self):
        self.login('demo_student_b_01', 'DEMO_FUTURE')
        self.assertEqual(self.client.get('/api/v1/timetable/today/').status_code, 200)
        self.assertEqual(self.client.post('/api/v1/timetable/bulk/', {'cells': []}, format='json').status_code, 403)

        self.login('demo_parent_multi', 'DEMO_FUTURE')
        linked_id = TimetableEntry.objects.filter(
            school__code='DEMO_FUTURE', teacher_assignment__classroom__student_enrollments__student__guardians__parent__user__username='demo_parent_multi',
        ).values_list('teacher_assignment__classroom__student_enrollments__student_id', flat=True).first()
        self.assertEqual(self.client.get('/api/v1/timetable/week/', {'student_id': linked_id}).status_code, 200)
        self.assertEqual(self.client.get('/api/v1/timetable/week/', {'student_id': 999999}).status_code, 404)

        self.login('demo_student_transferred', 'DEMO_NOOR')
        historical = self.client.get('/api/v1/timetable/week/')
        self.assertEqual(historical.status_code, 200, historical.data)
        self.assertTrue(any(day['entries'] for day in historical.data['days']))
        self.assertEqual(self.client.put('/api/v1/timetable/config/', {'working_days': [0]}).status_code, 403)

    def test_unauthenticated_invalid_filter_and_unsupported_method(self):
        self.assertEqual(self.client.get('/api/v1/timetable/today/').status_code, 401)
        self.login('demo_teacher_a', 'DEMO_NOOR')
        self.assertEqual(self.client.get('/api/v1/timetable/today/', {'weekday': 'bad'}).status_code, 400)
        self.assertEqual(self.client.delete('/api/v1/timetable/today/').status_code, 405)

    def test_teacher_today_query_budget(self):
        self.login('demo_teacher_multi', 'DEMO_NOOR')
        with self.assertNumQueries(8):
            response = self.client.get('/api/v1/timetable/today/', {'date': '2026-08-09'})
        self.assertEqual(response.status_code, 200, response.data)

    def test_attendance_shortcut_is_role_safe_and_daily_complete(self):
        day = timezone.datetime(2026, 8, 9).date()
        target_date = timezone.datetime.combine(day, timezone.datetime.min.time()).replace(hour=8)
        moment = timezone.make_aware(target_date)
        self.login('demo_teacher_multi', 'DEMO_NOOR')
        with patch('core.timetable_views.timezone.localtime', return_value=moment):
            teacher = self.client.get('/api/v1/timetable/today/', {'date': day.isoformat()})
        self.assertEqual(teacher.status_code, 200, teacher.data)
        self.assertTrue(any(row['can_take_attendance'] for row in teacher.data['entries']))
        first = TimetableEntry.objects.get(pk=teacher.data['entries'][0]['id'])
        term = AcademicTerm.objects.filter(
            school=first.school, academic_year=first.academic_year,
        ).order_by('start_date').first()
        AcademicTerm.objects.filter(pk=term.pk).update(
            start_date=first.academic_year.start_date, end_date=first.academic_year.end_date,
        )
        term.refresh_from_db()

        enrollments = list(StudentEnrollment.objects.filter(
            school=first.school, academic_year=first.academic_year,
            classroom=first.teacher_assignment.classroom,
            section=first.teacher_assignment.section, status='active', is_current=True,
        ))
        Attendance.objects.filter(
            student_enrollment__in=enrollments, attendance_date=target_date.date(),
        ).delete()
        with patch('core.timetable_views.timezone.localtime', return_value=moment):
            empty = self.client.get('/api/v1/timetable/today/', {'date': day.isoformat()})
        self.assertTrue(all(row['attendance_status'] == 'not_recorded' for row in empty.data['entries']))
        Attendance.objects.create(
            student_enrollment=enrollments[0], teacher_assignment=first.teacher_assignment,
            academic_term=term, attendance_date=target_date.date(), status='present',
        )
        with patch('core.timetable_views.timezone.localtime', return_value=moment):
            partial = self.client.get('/api/v1/timetable/today/', {'date': day.isoformat()})
        expected = len(enrollments)
        scoped_partial = [
            row for row in partial.data['entries']
            if row['classroom'] == first.teacher_assignment.classroom.name
            and row['section'] == first.teacher_assignment.section.name
        ]
        self.assertTrue(scoped_partial)
        self.assertTrue(all(row['attendance_count'] == 1 for row in scoped_partial))
        self.assertTrue(all(
            row['attendance_status'] == ('recorded' if expected == 1 else 'partial')
            for row in scoped_partial
        ))
        for enrollment in enrollments[1:]:
            Attendance.objects.create(
                student_enrollment=enrollment, teacher_assignment=first.teacher_assignment,
                academic_term=term, attendance_date=target_date.date(), status='present',
            )
        with patch('core.timetable_views.timezone.localtime', return_value=moment):
            complete = self.client.get('/api/v1/timetable/today/', {'date': day.isoformat()})
        scoped_complete = [
            row for row in complete.data['entries']
            if row['classroom'] == first.teacher_assignment.classroom.name
            and row['section'] == first.teacher_assignment.section.name
        ]
        self.assertTrue(all(row['attendance_status'] == 'recorded' for row in scoped_complete))
        self.assertTrue(all(row['attendance_expected_count'] == expected for row in scoped_complete))

        self.login('demo_student_b_01', 'DEMO_FUTURE')
        student = self.client.get('/api/v1/timetable/today/')
        self.assertTrue(all(not row['can_take_attendance'] for row in student.data['entries']))
        self.login('demo_parent_multi', 'DEMO_FUTURE')
        student_id = StudentEnrollment.objects.filter(
            school__code='DEMO_FUTURE',
            student__guardians__parent__user__username='demo_parent_multi',
        ).values_list('student_id', flat=True).first()
        parent = self.client.get('/api/v1/timetable/week/', {'student_id': student_id})
        self.assertTrue(all(
            not row['can_take_attendance']
            for day in parent.data['days'] for row in day['entries']
        ))

    def test_working_day_and_used_period_mutation_guards(self):
        self.login('demo_school_a_admin', 'DEMO_NOOR')
        entry = TimetableEntry.objects.filter(school__code='DEMO_NOOR').first()
        config = self.client.get('/api/v1/timetable/config/').data
        rejected_days = [day for day in config['working_days'] if day != entry.weekday]
        rejected = self.client.put(
            '/api/v1/timetable/config/', {'working_days': rejected_days}, format='json',
        )
        self.assertEqual(rejected.status_code, 400, rejected.data)
        unused = next(day for day in range(7) if day not in config['working_days'])
        accepted = self.client.put(
            '/api/v1/timetable/config/',
            {'working_days': config['working_days'] + [unused]}, format='json',
        )
        self.assertEqual(accepted.status_code, 200, accepted.data)

        period = entry.period
        changed = self.client.put(f'/api/v1/timetable/periods/{period.pk}/', {
            'name': period.name, 'sequence': period.sequence,
            'start_time': period.start_time, 'end_time': period.end_time,
            'kind': 'break', 'is_active': period.is_active,
        }, format='json')
        self.assertEqual(changed.status_code, 400, changed.data)
        deleted = self.client.delete(f'/api/v1/timetable/periods/{period.pk}/')
        self.assertEqual(deleted.status_code, 400, deleted.data)

    def test_bulk_final_state_clear_move_swap_and_atomic_conflict(self):
        self.login('demo_school_a_admin', 'DEMO_NOOR')
        seed_entry = TimetableEntry.objects.filter(
            school__code='DEMO_NOOR', weekday=0,
        ).order_by('-academic_year__is_active', 'period__sequence').first()
        entries = list(TimetableEntry.objects.filter(
            school=seed_entry.school, academic_year=seed_entry.academic_year, weekday=0,
        ).order_by('period__sequence')[:2])
        first, second = entries
        swap = self.client.post('/api/v1/timetable/bulk/', {'cells': [
            {
                'id': first.pk, 'teacher_assignment_id': first.teacher_assignment_id,
                'period_id': second.period_id, 'weekday': first.weekday,
            },
            {
                'id': second.pk, 'teacher_assignment_id': second.teacher_assignment_id,
                'period_id': first.period_id, 'weekday': second.weekday,
            },
        ]}, format='json')
        self.assertEqual(swap.status_code, 200, swap.data)
        first.refresh_from_db()

        moved_day = 4
        move = self.client.post('/api/v1/timetable/bulk/', {'cells': [
            {'id': first.pk, 'action': 'clear'},
            {
                'teacher_assignment_id': first.teacher_assignment_id,
                'period_id': first.period_id, 'weekday': moved_day,
            },
        ]}, format='json')
        self.assertEqual(move.status_code, 200, move.data)

        before = list(TimetableEntry.objects.values_list('id', 'weekday', 'period_id'))
        conflict_cell = {
            'teacher_assignment_id': second.teacher_assignment_id,
            'period_id': second.period_id, 'weekday': 3,
        }
        conflict = self.client.post('/api/v1/timetable/bulk/', {
            'cells': [conflict_cell, conflict_cell],
        }, format='json')
        self.assertEqual(conflict.status_code, 400, conflict.data)
        self.assertEqual(before, list(TimetableEntry.objects.values_list('id', 'weekday', 'period_id')))

    def test_copy_clear_target_preview_and_save_have_parity(self):
        self.login('demo_school_a_admin', 'DEMO_NOOR')
        entry = TimetableEntry.objects.filter(school__code='DEMO_NOOR', weekday=0).first()
        base = {
            'source_classroom_id': entry.teacher_assignment.classroom_id,
            'source_section_id': entry.teacher_assignment.section_id,
            'target_classroom_id': entry.teacher_assignment.classroom_id,
            'target_section_id': entry.teacher_assignment.section_id,
            'clear_target': True,
        }
        day_payload = {**base, 'source_weekday': 0, 'target_weekday': 1}
        before = TimetableEntry.objects.count()
        preview = self.client.post(
            '/api/v1/timetable/copy-day/', {**day_payload, 'validate_only': True}, format='json',
        )
        self.assertEqual(preview.status_code, 200, preview.data)
        self.assertTrue(preview.data['valid'])
        self.assertEqual(TimetableEntry.objects.count(), before)
        saved = self.client.post('/api/v1/timetable/copy-day/', day_payload, format='json')
        self.assertEqual(saved.status_code, 200, saved.data)

        before_week = TimetableEntry.objects.count()
        week_preview = self.client.post(
            '/api/v1/timetable/copy-week/', {**base, 'validate_only': True}, format='json',
        )
        self.assertEqual(week_preview.status_code, 200, week_preview.data)
        self.assertTrue(week_preview.data['valid'])
        self.assertEqual(TimetableEntry.objects.count(), before_week)
        week_saved = self.client.post('/api/v1/timetable/copy-week/', base, format='json')
        self.assertEqual(week_saved.status_code, 200, week_saved.data)
