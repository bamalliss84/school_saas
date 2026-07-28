from rest_framework import serializers
from .models import School, AcademicYear, User


class SchoolSerializer(serializers.ModelSerializer):
    class Meta:
        model = School
        fields = (
            'id',
            'name',
            'code',
            'phone',
            'email',
            'address',
            'is_active',
        )


class AcademicYearSerializer(serializers.ModelSerializer):
    school_name = serializers.CharField(source='school.name', read_only=True)

    class Meta:
        model = AcademicYear
        fields = (
            'id',
            'school',
            'school_name',
            'name',
            'start_date',
            'end_date',
            'is_active',
        )


class UserSerializer(serializers.ModelSerializer):
    school_name = serializers.CharField(source='school.name', read_only=True)
    academic_year_name = serializers.CharField(source='academic_year.name', read_only=True)

    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'email',
            'role',
            'school',
            'school_name',
            'academic_year',
            'academic_year_name',
            'phone',
            'is_active',
        )