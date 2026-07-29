from datetime import date

from django.core.exceptions import ValidationError
from django.test import RequestFactory, TestCase

from .mixins import SchoolQuerySetMixin
from .models import AcademicYear, School, User


class SchoolQuerySetMixinTests(TestCase):
    def setUp(self):
        self.school_a = School.objects.create(name='School A', code='A')
        self.school_b = School.objects.create(name='School B', code='B')
        self.user = User.objects.create_user(
            username='admin-a',
            password='test-password',
            role='school_admin',
            school=self.school_a,
        )

    def test_school_user_only_sees_own_school(self):
        request = RequestFactory().get('/api/schools/')
        request.user = self.user
        mixin = SchoolQuerySetMixin()
        mixin.request = request

        queryset = mixin.get_school_queryset(School.objects.all())

        self.assertEqual(list(queryset), [self.school_a])


class AcademicYearValidationTests(TestCase):
    def test_end_date_cannot_precede_start_date(self):
        school = School.objects.create(name='School A', code='A')
        academic_year = AcademicYear(
            school=school,
            name='Invalid Year',
            start_date=date(2026, 9, 1),
            end_date=date(2026, 8, 31),
        )

        with self.assertRaises(ValidationError):
            academic_year.full_clean()
