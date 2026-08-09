from datetime import timedelta

from django.db.models import Count
from django.utils import timezone
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework import generics, status
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import (
    Attendance, SchoolPeriod, SchoolTimetableConfig, StudentEnrollment,
    TeacherAssignment, TimetableEntry,
)
from .permissions import IsActiveSchoolUser
from .services.timetable import (
    bulk_apply, copy_schedule, replace_periods, require_timetable_admin, save_entry,
)
from .timetable_selectors import (
    active_entries_on, next_entry, periods_for_context, schedule_scope,
    timetable_weekday, today_entries,
)
from .timetable_serializers import (
    AssignmentOptionsQuerySerializer, CopyScheduleSerializer, PeriodBulkSerializer,
    SchoolPeriodSerializer, TimetableBulkSerializer, TimetableConfigSerializer,
    TimetableEntryInputSerializer, TimetableEntrySerializer, TimetableGridQuerySerializer,
    TimetableQuerySerializer,
)


def _admin(request):
    require_timetable_admin(request.active_membership)
    if request.active_academic_year is None:
        raise NotFound('Academic year was not found.')


def _entry_output(entry, *, request, date=None, now=None, attendance_states=None):
    data = TimetableEntrySerializer(entry).data
    now = now or timezone.localtime()
    if date == now.date():
        current_time = now.time().replace(tzinfo=None)
        if current_time >= entry.period.end_time:
            derived = 'finished'
        elif entry.period.start_time <= current_time < entry.period.end_time:
            derived = 'current'
        else:
            derived = 'upcoming'
    else:
        derived = 'upcoming' if date and date > now.date() else 'finished'
    data['status'] = derived
    key = (entry.teacher_assignment.classroom_id, entry.teacher_assignment.section_id)
    count, expected = (attendance_states or {}).get(key, (0, 0))
    if count == 0:
        attendance_status = 'not_recorded'
    elif expected and count >= expected:
        attendance_status = 'recorded'
    else:
        attendance_status = 'partial'
    data['attendance_status'] = attendance_status
    data['attendance_count'] = count
    data['attendance_expected_count'] = expected
    membership = request.active_membership
    assignment = entry.teacher_assignment
    data['can_take_attendance'] = bool(
        request.active_role == 'teacher'
        and membership is not None and membership.can_write
        and assignment.teacher.user_id == membership.user_id
        and assignment.is_current
        and date == now.date()
        and derived in ('current', 'upcoming')
        and (assignment.start_date is None or date >= assignment.start_date)
        and (assignment.end_date is None or date <= assignment.end_date)
    )
    return data


def _attendance_states(entries, date):
    scopes = {
        (entry.teacher_assignment.classroom_id, entry.teacher_assignment.section_id)
        for entry in entries
    }
    classroom_ids = {classroom_id for classroom_id, _ in scopes}
    section_ids = {section_id for _, section_id in scopes}
    if not scopes:
        return {}
    expected_rows = StudentEnrollment.objects.filter(
        classroom_id__in=classroom_ids, section_id__in=section_ids,
        academic_year_id=entries[0].academic_year_id, school_id=entries[0].school_id,
        status='active', is_current=True,
    ).values('classroom_id', 'section_id').annotate(total=Count('id'))
    attendance_rows = Attendance.objects.filter(
        student_enrollment__classroom_id__in=classroom_ids,
        student_enrollment__section_id__in=section_ids,
        student_enrollment__academic_year_id=entries[0].academic_year_id,
        student_enrollment__school_id=entries[0].school_id,
        attendance_date=date,
    ).values(
        'student_enrollment__classroom_id', 'student_enrollment__section_id',
    ).annotate(total=Count('id'))
    expected = {(row['classroom_id'], row['section_id']): row['total'] for row in expected_rows}
    counts = {
        (row['student_enrollment__classroom_id'], row['student_enrollment__section_id']): row['total']
        for row in attendance_rows
    }
    return {scope: (counts.get(scope, 0), expected.get(scope, 0)) for scope in scopes}


class TimetableConfigAPIView(APIView):
    permission_classes = (IsActiveSchoolUser,)

    @extend_schema(responses={200: TimetableConfigSerializer})
    def get(self, request):
        year = request.active_academic_year
        if year is None:
            raise NotFound('Academic year was not found.')
        item = SchoolTimetableConfig.objects.filter(
            school=request.active_school, academic_year=year,
        ).first()
        if item is None:
            return Response({
                'id': None, 'school': request.active_school.pk,
                'academic_year': year.pk, 'working_days': [0, 1, 2, 3, 4],
                'created_at': None, 'updated_at': None,
            })
        return Response(TimetableConfigSerializer(item).data)

    @extend_schema(request=TimetableConfigSerializer, responses={200: TimetableConfigSerializer})
    def put(self, request):
        _admin(request)
        item, _ = SchoolTimetableConfig.objects.get_or_create(
            school=request.active_school, academic_year=request.active_academic_year,
            defaults={'working_days': [0, 1, 2, 3, 4]},
        )
        serializer = TimetableConfigSerializer(item, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class PeriodListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = SchoolPeriodSerializer
    permission_classes = (IsActiveSchoolUser,)
    pagination_class = None

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return SchoolPeriod.objects.none()
        return periods_for_context(self.request)

    def perform_create(self, serializer):
        _admin(self.request)
        serializer.save(
            school=self.request.active_school, academic_year=self.request.active_academic_year,
        )


class PeriodDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = SchoolPeriodSerializer
    permission_classes = (IsActiveSchoolUser,)

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return SchoolPeriod.objects.none()
        return periods_for_context(self.request)

    def perform_update(self, serializer):
        _admin(self.request)
        serializer.save()

    def perform_destroy(self, instance):
        _admin(self.request)
        if instance.timetable_entries.exists():
            raise ValidationError('Used periods cannot be deleted; deactivate them instead.')
        instance.delete()


class PeriodBulkAPIView(APIView):
    permission_classes = (IsActiveSchoolUser,)

    @extend_schema(request=PeriodBulkSerializer, responses={200: SchoolPeriodSerializer(many=True)})
    def post(self, request):
        _admin(request)
        payload = PeriodBulkSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        items = replace_periods(
            membership=request.active_membership, academic_year=request.active_academic_year,
            rows=payload.validated_data['periods'],
        )
        return Response(SchoolPeriodSerializer(items, many=True).data)


class EntryListCreateAPIView(generics.ListAPIView):
    serializer_class = TimetableEntrySerializer
    permission_classes = (IsActiveSchoolUser,)

    def _params(self):
        payload = TimetableQuerySerializer(data=self.request.query_params)
        payload.is_valid(raise_exception=True)
        return payload.validated_data

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return TimetableEntry.objects.none()
        params = self._params()
        queryset = schedule_scope(
            self.request, student_id=params.get('student_id'), teacher_id=params.get('teacher'),
            classroom_id=params.get('classroom'), section_id=params.get('section'),
        )
        mapping = {
            'weekday': 'weekday', 'teacher_assignment': 'teacher_assignment_id',
            'subject': 'teacher_assignment__subject_id', 'period': 'period_id',
            'is_active': 'is_active',
        }
        for key, lookup in mapping.items():
            if key in params:
                queryset = queryset.filter(**{lookup: params[key]})
        if params.get('date'):
            queryset = active_entries_on(queryset, params['date']).filter(
                weekday=timetable_weekday(params['date']),
            )
        return queryset.order_by('weekday', 'period__sequence', 'pk')

    @extend_schema(request=TimetableEntryInputSerializer, responses={201: TimetableEntrySerializer})
    def post(self, request):
        _admin(request)
        payload = TimetableEntryInputSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        item = save_entry(
            membership=request.active_membership, academic_year=request.active_academic_year,
            values=payload.validated_data,
        )
        return Response(TimetableEntrySerializer(item).data, status=status.HTTP_201_CREATED)


class EntryDetailAPIView(APIView):
    permission_classes = (IsActiveSchoolUser,)
    serializer_class = TimetableEntrySerializer

    def item(self, request, pk):
        return generics.get_object_or_404(schedule_scope(request), pk=pk)

    @extend_schema(responses={200: TimetableEntrySerializer})
    def get(self, request, pk):
        return Response(TimetableEntrySerializer(self.item(request, pk)).data)

    @extend_schema(request=TimetableEntryInputSerializer, responses={200: TimetableEntrySerializer})
    def put(self, request, pk):
        _admin(request)
        item = self.item(request, pk)
        payload = TimetableEntryInputSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        saved = save_entry(
            membership=request.active_membership, academic_year=request.active_academic_year,
            values=payload.validated_data, instance=item,
        )
        return Response(TimetableEntrySerializer(saved).data)

    def delete(self, request, pk):
        _admin(request)
        self.item(request, pk).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class BulkTimetableAPIView(APIView):
    permission_classes = (IsActiveSchoolUser,)

    @extend_schema(request=TimetableBulkSerializer, responses={200: OpenApiTypes.OBJECT})
    def post(self, request):
        _admin(request)
        payload = TimetableBulkSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        result = bulk_apply(
            membership=request.active_membership, academic_year=request.active_academic_year,
            cells=payload.validated_data['cells'],
            validate_only=payload.validated_data['validate_only'],
        )
        if 'entries' in result:
            result['entries'] = TimetableEntrySerializer(result['entries'], many=True).data
        return Response(result)


class ValidateTimetableAPIView(BulkTimetableAPIView):
    serializer_class = TimetableBulkSerializer

    def post(self, request):
        _admin(request)
        data = request.data.copy()
        data['validate_only'] = True
        payload = TimetableBulkSerializer(data=data)
        payload.is_valid(raise_exception=True)
        return Response(bulk_apply(
            membership=request.active_membership,
            academic_year=request.active_academic_year,
            cells=payload.validated_data['cells'], validate_only=True,
        ))


class GridAPIView(APIView):
    permission_classes = (IsActiveSchoolUser,)

    @extend_schema(parameters=[TimetableGridQuerySerializer], responses={200: OpenApiTypes.OBJECT})
    def get(self, request):
        if request.active_role not in ('school_admin', 'super_admin'):
            raise PermissionDenied('School administrator access is required.')
        params = TimetableGridQuerySerializer(data=request.query_params)
        params.is_valid(raise_exception=True)
        data = params.validated_data
        queryset = schedule_scope(
            request, classroom_id=data['classroom_id'], section_id=data['section_id'],
        )
        if data.get('date'):
            queryset = active_entries_on(queryset, data['date'])
        config = SchoolTimetableConfig.objects.filter(
            school=request.active_school, academic_year=request.active_academic_year,
        ).first()
        working_days = config.working_days if config else [0, 1, 2, 3, 4]
        return Response({
            'days': [
                {'value': day, 'label': dict(SchoolTimetableConfig.WEEKDAY_CHOICES)[day]}
                for day in working_days
            ],
            'periods': SchoolPeriodSerializer(periods_for_context(request), many=True).data,
            'entries': TimetableEntrySerializer(queryset.order_by('weekday', 'period__sequence'), many=True).data,
        })


class AssignmentOptionsAPIView(APIView):
    permission_classes = (IsActiveSchoolUser,)

    @extend_schema(parameters=[AssignmentOptionsQuerySerializer], responses={200: OpenApiTypes.OBJECT})
    def get(self, request):
        if request.active_role not in ('school_admin', 'super_admin'):
            raise PermissionDenied('School administrator access is required.')
        payload = AssignmentOptionsQuerySerializer(data=request.query_params)
        payload.is_valid(raise_exception=True)
        data = payload.validated_data
        rows = TeacherAssignment.objects.filter(
            school=request.active_school, academic_year=request.active_academic_year,
            classroom_id=data['classroom_id'], section_id=data['section_id'], is_current=True,
        ).select_related('teacher', 'subject').order_by('subject__name', 'teacher__full_name')
        return Response([{
            'id': row.pk, 'teacher': row.teacher.full_name, 'subject': row.subject.name,
            'label': f'{row.teacher.full_name} — {row.subject.name}',
        } for row in rows])


class CopyAPIView(APIView):
    permission_classes = (IsActiveSchoolUser,)
    mode = 'day'

    @extend_schema(request=CopyScheduleSerializer, responses={200: OpenApiTypes.OBJECT})
    def post(self, request):
        _admin(request)
        payload = CopyScheduleSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        data = payload.validated_data
        if self.mode == 'day' and ('source_weekday' not in data or 'target_weekday' not in data):
            raise ValidationError('Copy day requires source_weekday and target_weekday.')
        if self.mode == 'week':
            data.pop('source_weekday', None)
            data.pop('target_weekday', None)
        result = copy_schedule(
            membership=request.active_membership, academic_year=request.active_academic_year,
            **data,
        )
        if 'entries' in result:
            result['entries'] = TimetableEntrySerializer(result['entries'], many=True).data
        return Response(result)


class CopyDayAPIView(CopyAPIView):
    mode = 'day'


class CopyWeekAPIView(CopyAPIView):
    mode = 'week'


class TimelineAPIView(APIView):
    permission_classes = (IsActiveSchoolUser,)
    mode = 'today'

    def _query(self, request):
        payload = TimetableQuerySerializer(data=request.query_params)
        payload.is_valid(raise_exception=True)
        return payload.validated_data

    @extend_schema(parameters=[TimetableQuerySerializer], responses={200: OpenApiTypes.OBJECT})
    def get(self, request):
        params = self._query(request)
        student_id = params.get('student_id')
        scope = {
            'student_id': student_id, 'teacher_id': params.get('teacher'),
            'classroom_id': params.get('classroom'), 'section_id': params.get('section'),
        }
        date = params.get('date') or timezone.localdate()
        now = timezone.localtime()
        if self.mode == 'week':
            start = date - timedelta(days=timetable_weekday(date))
            rows = []
            for offset in range(7):
                day = start + timedelta(days=offset)
                entries = list(active_entries_on(
                    schedule_scope(request, **scope).filter(weekday=timetable_weekday(day)), day,
                ).order_by('period__sequence', 'pk'))
                rows.append({'date': day, 'weekday': timetable_weekday(day), 'entries': [
                    _entry_output(entry, request=request, date=day, now=now) for entry in entries
                ]})
            return Response({'week_start': start, 'days': rows})
        entries, date = today_entries(request, date=date, **scope)
        entries = list(entries.order_by('period__sequence', 'pk'))
        states = _attendance_states(entries, date)
        output = [
            _entry_output(entry, request=request, date=date, now=now, attendance_states=states)
            for entry in entries
        ]
        current = next((item for item in output if item['status'] == 'current'), None)
        future = next((item for item in output if item['status'] == 'upcoming'), None)
        if self.mode == 'current':
            return Response({'date': date, 'current_entry': current})
        if self.mode == 'next':
            entry, next_date = next_entry(request, now=now, **scope)
            return Response({'date': next_date, 'next_entry': _entry_output(entry, request=request, date=next_date, now=now) if entry else None})
        periods = SchoolPeriodSerializer(periods_for_context(request), many=True).data
        return Response({
            'date': date, 'weekday': timetable_weekday(date), 'current_entry': current,
            'next_entry': future, 'entries': output, 'periods': periods,
        })


class TodayAPIView(TimelineAPIView):
    mode = 'today'


class WeekAPIView(TimelineAPIView):
    mode = 'week'


class CurrentAPIView(TimelineAPIView):
    mode = 'current'


class NextAPIView(TimelineAPIView):
    mode = 'next'
