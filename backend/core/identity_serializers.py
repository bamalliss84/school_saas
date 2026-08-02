from rest_framework import serializers

from .models import (
    AcademicYear, Classroom, School, Section, StudentEnrollment,
)


class StudentTransferSerializer(serializers.Serializer):
    destination_school = serializers.PrimaryKeyRelatedField(queryset=School.objects.all())
    destination_academic_year = serializers.PrimaryKeyRelatedField(queryset=AcademicYear.objects.all())
    destination_classroom = serializers.PrimaryKeyRelatedField(queryset=Classroom.objects.all())
    destination_section = serializers.PrimaryKeyRelatedField(queryset=Section.objects.all())
    transfer_date = serializers.DateField()
    reason = serializers.CharField(allow_blank=False)


class AcademicHistoryQuerySerializer(serializers.Serializer):
    school_membership_id = serializers.IntegerField(required=False, min_value=1)
    school_id = serializers.IntegerField(required=False, min_value=1)
    academic_year_id = serializers.IntegerField(required=False, min_value=1)

    def validate(self, attrs):
        if attrs.get('school_membership_id') and attrs.get('school_id'):
            raise serializers.ValidationError('Use either school_membership_id or school_id.')
        return attrs


class StudentSchoolHistorySerializer(serializers.Serializer):
    school = serializers.DictField()
    access_mode = serializers.ChoiceField(choices=('read_write', 'read_only'))
    is_current = serializers.BooleanField()
    membership_id = serializers.IntegerField(allow_null=True)
    academic_years = serializers.ListField(child=serializers.DictField())