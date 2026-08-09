from rest_framework import serializers

from .models import SchoolPeriod, SchoolTimetableConfig, TimetableEntry


class TimetableConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = SchoolTimetableConfig
        fields = ('id', 'school', 'academic_year', 'working_days', 'created_at', 'updated_at')
        read_only_fields = ('id', 'school', 'academic_year', 'created_at', 'updated_at')

    def validate_working_days(self, value):
        if self.instance is None:
            return value
        removed = set(self.instance.working_days) - set(value)
        used = set(TimetableEntry.objects.filter(
            school_id=self.instance.school_id,
            academic_year_id=self.instance.academic_year_id,
            weekday__in=removed,
        ).values_list('weekday', flat=True).distinct())
        if used:
            labels = dict(SchoolTimetableConfig.WEEKDAY_CHOICES)
            raise serializers.ValidationError({
                'code': 'working_days_in_use',
                'days': [
                    {'value': day, 'label': labels[day]}
                    for day in sorted(used)
                ],
                'message': 'لا يمكن إزالة أيام عليها حصص مسجلة. امسح الحصص أولاً.',
            })
        return value


class SchoolPeriodSerializer(serializers.ModelSerializer):
    class Meta:
        model = SchoolPeriod
        fields = (
            'id', 'school', 'academic_year', 'name', 'sequence', 'start_time',
            'end_time', 'kind', 'is_active', 'created_at', 'updated_at',
        )
        read_only_fields = ('id', 'school', 'academic_year', 'created_at', 'updated_at')

    def validate(self, attrs):
        instance = self.instance
        if (
            instance is not None
            and instance.timetable_entries.exists()
            and attrs.get('kind', instance.kind) != 'lesson'
        ):
            raise serializers.ValidationError({
                'kind': 'لا يمكن تحويل فترة مستخدمة في الجدول إلى استراحة.',
            })
        return attrs


class PeriodInputSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=100)
    sequence = serializers.IntegerField(min_value=0, max_value=32767)
    start_time = serializers.TimeField()
    end_time = serializers.TimeField()
    kind = serializers.ChoiceField(choices=SchoolPeriod.KIND_CHOICES, default='lesson')
    is_active = serializers.BooleanField(default=True)


class PeriodBulkSerializer(serializers.Serializer):
    periods = PeriodInputSerializer(many=True, allow_empty=False)


class TimetableEntrySerializer(serializers.ModelSerializer):
    teacher = serializers.CharField(source='teacher_assignment.teacher.full_name', read_only=True)
    classroom = serializers.CharField(source='teacher_assignment.classroom.name', read_only=True)
    section = serializers.CharField(source='teacher_assignment.section.name', read_only=True)
    subject = serializers.CharField(source='teacher_assignment.subject.name', read_only=True)
    period_detail = SchoolPeriodSerializer(source='period', read_only=True)

    class Meta:
        model = TimetableEntry
        fields = (
            'id', 'school', 'academic_year', 'teacher_assignment', 'teacher',
            'classroom', 'section', 'subject', 'weekday', 'period', 'period_detail',
            'room_or_location', 'valid_from', 'valid_to', 'is_active',
            'created_at', 'updated_at',
        )
        read_only_fields = (
            'id', 'school', 'academic_year', 'teacher', 'classroom', 'section',
            'subject', 'period_detail', 'created_at', 'updated_at',
        )


class TimetableEntryInputSerializer(serializers.Serializer):
    teacher_assignment_id = serializers.IntegerField(min_value=1)
    period_id = serializers.IntegerField(min_value=1)
    weekday = serializers.ChoiceField(choices=TimetableEntry.WEEKDAY_CHOICES)
    room_or_location = serializers.CharField(max_length=120, required=False, allow_blank=True, default='')
    valid_from = serializers.DateField(required=False, allow_null=True)
    valid_to = serializers.DateField(required=False, allow_null=True)
    is_active = serializers.BooleanField(required=False, default=True)


class TimetableCellSerializer(TimetableEntryInputSerializer):
    id = serializers.IntegerField(min_value=1, required=False)
    action = serializers.ChoiceField(choices=('upsert', 'clear'), default='upsert')
    teacher_assignment_id = serializers.IntegerField(min_value=1, required=False)
    period_id = serializers.IntegerField(min_value=1, required=False)
    weekday = serializers.ChoiceField(choices=TimetableEntry.WEEKDAY_CHOICES, required=False)

    def validate(self, attrs):
        if attrs.get('action') != 'clear':
            missing = {
                field for field in ('teacher_assignment_id', 'period_id', 'weekday')
                if field not in attrs
            }
            if missing:
                raise serializers.ValidationError({field: 'This field is required.' for field in missing})
        return attrs


class TimetableBulkSerializer(serializers.Serializer):
    cells = TimetableCellSerializer(many=True, allow_empty=False)
    validate_only = serializers.BooleanField(default=False)


class TimetableQuerySerializer(serializers.Serializer):
    date = serializers.DateField(required=False)
    weekday = serializers.ChoiceField(choices=TimetableEntry.WEEKDAY_CHOICES, required=False)
    teacher_assignment = serializers.IntegerField(min_value=1, required=False)
    teacher = serializers.IntegerField(min_value=1, required=False)
    classroom = serializers.IntegerField(min_value=1, required=False)
    section = serializers.IntegerField(min_value=1, required=False)
    subject = serializers.IntegerField(min_value=1, required=False)
    period = serializers.IntegerField(min_value=1, required=False)
    student_id = serializers.IntegerField(min_value=1, required=False)
    is_active = serializers.BooleanField(required=False)


class TimetableGridQuerySerializer(serializers.Serializer):
    classroom_id = serializers.IntegerField(min_value=1)
    section_id = serializers.IntegerField(min_value=1)
    date = serializers.DateField(required=False)


class AssignmentOptionsQuerySerializer(serializers.Serializer):
    classroom_id = serializers.IntegerField(min_value=1)
    section_id = serializers.IntegerField(min_value=1)


class CopyScheduleSerializer(serializers.Serializer):
    source_classroom_id = serializers.IntegerField(min_value=1)
    source_section_id = serializers.IntegerField(min_value=1)
    target_classroom_id = serializers.IntegerField(min_value=1, required=False)
    target_section_id = serializers.IntegerField(min_value=1, required=False)
    source_weekday = serializers.IntegerField(min_value=0, max_value=6, required=False)
    target_weekday = serializers.IntegerField(min_value=0, max_value=6, required=False)
    clear_target = serializers.BooleanField(default=False)
    validate_only = serializers.BooleanField(default=False)
