import os
import uuid

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.utils import timezone

class School(models.Model):
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=50, unique=True)

    phone = models.CharField(max_length=30, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)

    address = models.TextField(blank=True, null=True)

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
    
class AcademicYear(models.Model):
    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name='academic_years'
    )

    name = models.CharField(max_length=100)
    start_date = models.DateField()
    end_date = models.DateField()

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('school', 'name')

    def clean(self):
        if self.start_date and self.end_date and self.start_date > self.end_date:
            raise ValidationError('Academic year start date must be before end date.')

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.school.name} - {self.name}"

class SchoolSetting(models.Model):
    school = models.OneToOneField(
        School,
        on_delete=models.CASCADE,
        related_name='settings'
    )

    school_name_ar = models.CharField(max_length=255)
    school_name_en = models.CharField(max_length=255, blank=True, null=True)

    logo = models.ImageField(
        upload_to='school_logos/',
        blank=True,
        null=True
    )

    primary_color = models.CharField(
        max_length=20,
        default='#1976D2'
    )

    language = models.CharField(
        max_length=20,
        default='ar'
    )

    timezone = models.CharField(
        max_length=100,
        default='Asia/Riyadh'
    )

    allow_parent_notifications = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.school.name} Settings"

class User(AbstractUser):

    ROLE_CHOICES = (
        ('super_admin', 'Super Admin'),
        ('school_admin', 'School Admin'),
        ('teacher', 'Teacher'),
        ('parent', 'Parent'),
        ('student', 'Student'),
    )

    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name='users'
    )

    academic_year = models.ForeignKey(
        AcademicYear,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )

    role = models.CharField(
        max_length=50,
        choices=ROLE_CHOICES,
        default='student'
    )

    phone = models.CharField(
        max_length=30,
        blank=True,
        null=True
    )

    is_active_school_user = models.BooleanField(default=True)

    def clean(self):
        super().clean()

        if not self.is_superuser and self.role != 'super_admin' and not self.school_id:
            raise ValidationError('A school is required for non-super-admin users.')

        if self.academic_year_id and self.school_id:
            if self.academic_year.school_id != self.school_id:
                raise ValidationError('Academic year must belong to the selected school.')

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.username


class SchoolMembership(models.Model):
    ROLE_CHOICES = User.ROLE_CHOICES
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('historical', 'Historical'),
        ('suspended', 'Suspended'),
        ('ended', 'Ended'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='school_memberships')
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='memberships')
    role = models.CharField(max_length=50, choices=ROLE_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)
    is_default = models.BooleanField(default=False)
    last_used_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('user_id', '-is_default', 'school_id', 'role')
        constraints = [
            models.UniqueConstraint(fields=('user', 'school', 'role'), name='unique_user_school_role_membership'),
            models.UniqueConstraint(
                fields=('user',), condition=models.Q(role='student', status='active'),
                name='unique_active_student_membership',
            ),
            models.UniqueConstraint(
                fields=('user',), condition=models.Q(is_default=True),
                name='unique_default_membership_per_user',
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(start_date__isnull=True) | models.Q(end_date__isnull=True)
                    | models.Q(start_date__lte=models.F('end_date'))
                ),
                name='membership_dates_in_order',
            ),
            models.CheckConstraint(
                condition=models.Q(is_default=False) | models.Q(status='active'),
                name='default_membership_must_be_active',
            ),
        ]

    @property
    def access_mode(self):
        if not self.school.is_active or self.status in ('suspended', 'ended'):
            return 'unavailable'
        if self.status == 'historical':
            return 'read_only'
        return 'read_write'

    @property
    def can_read(self):
        return self.access_mode in ('read_write', 'read_only')

    @property
    def can_write(self):
        return self.access_mode == 'read_write'

    def clean(self):
        if self.is_default and self.status != 'active':
            raise ValidationError('Only an active membership can be default.')
        if self.start_date and self.end_date and self.start_date > self.end_date:
            raise ValidationError('Membership start date must not follow end date.')

    def save(self, *args, **kwargs):
        if self.is_default:
            SchoolMembership.objects.filter(user_id=self.user_id, is_default=True).exclude(
                pk=self.pk,
            ).update(is_default=False)
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.user} - {self.school} - {self.role}'

class Classroom(models.Model):
    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name='classrooms'
    )

    academic_year = models.ForeignKey(
        AcademicYear,
        on_delete=models.CASCADE,
        related_name='classrooms'
    )

    name = models.CharField(max_length=100)
    code = models.CharField(max_length=50)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('school', 'academic_year', 'code')

    def __str__(self):
        return f"{self.name} - {self.academic_year.name}"


class Section(models.Model):
    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name='sections'
    )

    academic_year = models.ForeignKey(
        AcademicYear,
        on_delete=models.CASCADE,
        related_name='sections'
    )

    classroom = models.ForeignKey(
        Classroom,
        on_delete=models.CASCADE,
        related_name='sections'
    )

    name = models.CharField(max_length=100)
    code = models.CharField(max_length=50)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('school', 'academic_year', 'classroom', 'code')

    def __str__(self):
        return f"{self.classroom.name} - {self.name}"

class Subject(models.Model):
    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name='subjects'
    )

    name = models.CharField(max_length=200)
    code = models.CharField(max_length=50)

    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class ClassSubject(models.Model):
    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE
    )

    academic_year = models.ForeignKey(
        AcademicYear,
        on_delete=models.CASCADE
    )

    classroom = models.ForeignKey(
        Classroom,
        on_delete=models.CASCADE,
        related_name='class_subjects'
    )

    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name='class_subjects'
    )

    weekly_periods = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = (
            'academic_year',
            'classroom',
            'subject'
        )

    def clean(self):
        if self.academic_year.school_id != self.school_id:
            raise ValidationError('Academic year must belong to the selected school.')
        if self.classroom.school_id != self.school_id:
            raise ValidationError('Classroom must belong to the selected school.')
        if self.classroom.academic_year_id != self.academic_year_id:
            raise ValidationError('Classroom academic year must match the selected academic year.')
        if self.subject.school_id != self.school_id:
            raise ValidationError('Subject must belong to the selected school.')

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.classroom} - {self.subject}"
    
class Teacher(models.Model):
    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name='teachers'
    )

    academic_year = models.ForeignKey(
        AcademicYear,
        on_delete=models.CASCADE,
        related_name='teachers'
    )

    user = models.OneToOneField(
        User,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='teacher_profile'
    )

    employee_code = models.CharField(
        max_length=50,
        unique=True,
        editable=False
    )
    full_name = models.CharField(max_length=255)

    phone = models.CharField(
        max_length=30,
        blank=True,
        null=True
    )

    email = models.EmailField(
        blank=True,
        null=True
    )

    specialization = models.CharField(
        max_length=150,
        blank=True,
        null=True
    )

    qualification = models.CharField(
        max_length=150,
        blank=True,
        null=True
    )

    hire_date = models.DateField(
        blank=True,
        null=True
    )

    address = models.TextField(
        blank=True,
        null=True
    )

    photo = models.ImageField(
        upload_to='teacher_photos/',
        blank=True,
        null=True
    )

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=[
                    'school',
                    'academic_year',
                    'employee_code'
                ],
                name='unique_teacher_employee_code'
            )
        ]
    def save(self, *args, **kwargs):
        if not self.employee_code:
            school_code = self.school.code.upper()

            last_teacher = Teacher.objects.filter(
                school=self.school,
                academic_year=self.academic_year
            ).order_by('-id').first()

            next_number = 1

            if last_teacher and last_teacher.employee_code:
                try:
                    next_number = int(
                        last_teacher.employee_code.split('-')[-1].removeprefix('T')
                    ) + 1
                except Exception:
                    next_number = 1

            self.employee_code = (
                f"{school_code}-"
                f"T{str(next_number).zfill(5)}"
            )

        super().save(*args, **kwargs)

    def __str__(self):
        return self.full_name
    
class Parent(models.Model):
    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name='parents'
    )

    user = models.OneToOneField(
        User,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='parent_profile'
    )

    parent_code = models.CharField(
        max_length=50,
        unique=True,
        editable=False
    )

    full_name = models.CharField(max_length=255)

    national_id = models.CharField(
        max_length=50,
        blank=True,
        null=True
    )

    phone = models.CharField(
        max_length=30,
        blank=True,
        null=True
    )

    email = models.EmailField(
        blank=True,
        null=True
    )

    address = models.TextField(
        blank=True,
        null=True
    )

    occupation = models.CharField(
        max_length=150,
        blank=True,
        null=True
    )

    workplace = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.parent_code:
            school_code = self.school.code.upper()

            last_parent = Parent.objects.filter(
                school=self.school
            ).order_by('-id').first()

            next_number = 1

            if last_parent and last_parent.parent_code:
                try:
                    next_number = int(
                        last_parent.parent_code.split('-')[-1]
                    ) + 1
                except Exception:
                    next_number = 1

            self.parent_code = (
                f"{school_code}-P{str(next_number).zfill(5)}"
            )

        super().save(*args, **kwargs)

    def __str__(self):
        return self.full_name

class Student(models.Model):
    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name='students'
    )

    user = models.OneToOneField(
        User,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='student_profile'
    )

    student_code = models.CharField(
        max_length=50,
        unique=True,
        editable=False
    )

    full_name = models.CharField(max_length=255)

    gender = models.CharField(
        max_length=10,
        choices=(
            ('male', 'Male'),
            ('female', 'Female'),
        )
    )

    birth_date = models.DateField(blank=True, null=True)

    photo = models.ImageField(
        upload_to='student_photos/',
        blank=True,
        null=True
    )

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def current_enrollment(self):
        return self.enrollments.filter(
            is_current=True,
            status='active'
        ).first()

    def save(self, *args, **kwargs):
        if not self.student_code:
            school_code = self.school.code.upper()

            last_student = Student.objects.filter(
                school=self.school
            ).order_by('-id').first()

            next_number = 1

            if last_student and last_student.student_code:
                try:
                    next_number = int(
                        last_student.student_code.split('-')[-1].replace('S', '')
                    ) + 1
                except Exception:
                    next_number = 1

            self.student_code = f"{school_code}-S{str(next_number).zfill(5)}"

        super().save(*args, **kwargs)

    def __str__(self):
        return self.full_name


class StudentEnrollment(models.Model):
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('transferred', 'Transferred'),
        ('graduated', 'Graduated'),
        ('withdrawn', 'Withdrawn'),
        ('suspended', 'Suspended'),
    )

    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name='enrollments'
    )

    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name='student_enrollments'
    )

    academic_year = models.ForeignKey(
        AcademicYear,
        on_delete=models.CASCADE,
        related_name='student_enrollments'
    )

    classroom = models.ForeignKey(
        Classroom,
        on_delete=models.CASCADE,
        related_name='student_enrollments'
    )

    section = models.ForeignKey(
        Section,
        on_delete=models.CASCADE,
        related_name='student_enrollments'
    )

    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default='active'
    )

    is_current = models.BooleanField(default=True)

    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['student', 'academic_year'],
                name='unique_student_academic_year_enrollment'
            ),
            models.UniqueConstraint(
                fields=['student'], condition=models.Q(is_current=True),
                name='unique_current_enrollment_per_student',
            ),
            models.CheckConstraint(
                condition=models.Q(is_current=False) | models.Q(status='active'),
                name='current_enrollment_must_be_active',
            ),
        ]

    def clean(self):

        if self.classroom.school_id != self.school_id:
            raise ValidationError('Classroom school must match enrollment school.')

        if self.section.school_id != self.school_id:
            raise ValidationError('Section school must match enrollment school.')

        if self.classroom.academic_year_id != self.academic_year_id:
            raise ValidationError('Classroom academic year must match enrollment academic year.')

        if self.section.academic_year_id != self.academic_year_id:
            raise ValidationError('Section academic year must match enrollment academic year.')

        if self.section.classroom_id != self.classroom_id:
            raise ValidationError('Section must belong to the selected classroom.')

    def save(self, *args, **kwargs):
        self.full_clean()

        if self.is_current:
            StudentEnrollment.objects.filter(
                student=self.student,
                is_current=True
            ).exclude(pk=self.pk).update(is_current=False)

        super().save(*args, **kwargs)
        if self.is_current and self.status == 'active' and self.student.school_id != self.school_id:
            Student.objects.filter(pk=self.student_id).update(school_id=self.school_id)
            self.student.school_id = self.school_id

    def __str__(self):
        return f"{self.student.full_name} - {self.academic_year.name} - {self.classroom.name}"
    
class StudentGuardian(models.Model):
    RELATION_CHOICES = (
        ('father', 'Father'),
        ('mother', 'Mother'),
        ('brother', 'Brother'),
        ('sister', 'Sister'),
        ('guardian', 'Guardian'),
        ('other', 'Other'),
    )

    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name='guardians'
    )

    parent = models.ForeignKey(
        Parent,
        on_delete=models.CASCADE,
        related_name='students'
    )

    relationship = models.CharField(
        max_length=30,
        choices=RELATION_CHOICES
    )

    is_primary = models.BooleanField(default=False)

    can_receive_notifications = models.BooleanField(default=True)
    can_receive_financial_alerts = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['student', 'parent'],
                name='unique_student_parent_guardian'
            )
        ]

    def save(self, *args, **kwargs):
        self.full_clean()

        if self.is_primary:
            StudentGuardian.objects.filter(
                student=self.student,
                is_primary=True
            ).exclude(pk=self.pk).update(is_primary=False)

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.student.full_name} - {self.parent.full_name} - {self.relationship}"

class TeacherAssignment(models.Model):
    teacher = models.ForeignKey(
        Teacher,
        on_delete=models.CASCADE,
        related_name='assignments'
    )

    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name='teacher_assignments'
    )

    academic_year = models.ForeignKey(
        AcademicYear,
        on_delete=models.CASCADE,
        related_name='teacher_assignments'
    )

    classroom = models.ForeignKey(
        Classroom,
        on_delete=models.CASCADE,
        related_name='teacher_assignments'
    )

    section = models.ForeignKey(
        Section,
        on_delete=models.CASCADE,
        related_name='teacher_assignments'
    )

    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name='teacher_assignments'
    )

    is_current = models.BooleanField(default=True)

    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=[
                    'teacher',
                    'academic_year',
                    'classroom',
                    'section',
                    'subject'
                ],
                name='unique_teacher_assignment'
            )
        ]

    def clean(self):
        if self.teacher.user_id:
            memberships = SchoolMembership.objects.filter(
                user_id=self.teacher.user_id, role='teacher',
            )
            if memberships.exists() and not memberships.filter(
                school_id=self.school_id, status='active',
            ).exists():
                raise ValidationError('Teacher requires an active membership in assignment school.')
            if not memberships.exists() and self.teacher.school_id != self.school_id:
                raise ValidationError('Teacher school must match assignment school for legacy users.')

        if self.classroom.school_id != self.school_id:
            raise ValidationError('Classroom school must match assignment school.')

        if self.section.school_id != self.school_id:
            raise ValidationError('Section school must match assignment school.')

        if self.subject.school_id != self.school_id:
            raise ValidationError('Subject school must match assignment school.')

        if self.classroom.academic_year_id != self.academic_year_id:
            raise ValidationError('Classroom academic year must match assignment academic year.')

        if self.section.academic_year_id != self.academic_year_id:
            raise ValidationError('Section academic year must match assignment academic year.')

        if self.section.classroom_id != self.classroom_id:
            raise ValidationError('Section must belong to the selected classroom.')

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.teacher.full_name} - {self.subject.name} - {self.classroom.name} - {self.section.name}"
    

class AcademicTerm(models.Model):
    TERM_CHOICES = (
        ('term_1', 'Term 1'),
        ('term_2', 'Term 2'),
        ('term_3', 'Term 3'),
        ('summer', 'Summer'),
    )

    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name='academic_terms'
    )

    academic_year = models.ForeignKey(
        AcademicYear,
        on_delete=models.CASCADE,
        related_name='terms'
    )

    name = models.CharField(max_length=100)

    term_type = models.CharField(
        max_length=30,
        choices=TERM_CHOICES
    )

    start_date = models.DateField()
    end_date = models.DateField()

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['school', 'academic_year', 'term_type'],
                name='unique_school_year_term'
            )
        ]

    def clean(self):
        if self.academic_year.school_id != self.school_id:
            raise ValidationError('Academic year must belong to the selected school.')
        if self.start_date and self.end_date and self.start_date > self.end_date:
            raise ValidationError('Academic term start date must be before end date.')
        if self.start_date and self.start_date < self.academic_year.start_date:
            raise ValidationError('Academic term cannot start before the academic year.')
        if self.end_date and self.end_date > self.academic_year.end_date:
            raise ValidationError('Academic term cannot end after the academic year.')

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.academic_year.name} - {self.name}"
    
class Attendance(models.Model):
    STATUS_CHOICES = (
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('late', 'Late'),
        ('excused', 'Excused'),
    )

    student_enrollment = models.ForeignKey(
        StudentEnrollment,
        on_delete=models.CASCADE,
        related_name='attendances'
    )

    teacher_assignment = models.ForeignKey(
        TeacherAssignment,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='attendances'
    )

    academic_term = models.ForeignKey(
        AcademicTerm,
        on_delete=models.CASCADE,
        related_name='attendances'
    )

    attendance_date = models.DateField()

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='present'
    )

    note = models.TextField(
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['student_enrollment', 'attendance_date'],
                name='unique_student_attendance_per_day'
            )
        ]

    def clean(self):
        if self.academic_term.academic_year_id != self.student_enrollment.academic_year_id:
            raise ValidationError('Academic term must match student academic year.')

        if self.teacher_assignment:
            if self.teacher_assignment.school_id != self.student_enrollment.school_id:
                raise ValidationError('Teacher assignment school must match student school.')

            if self.teacher_assignment.academic_year_id != self.student_enrollment.academic_year_id:
                raise ValidationError('Teacher assignment academic year must match student academic year.')

            if self.teacher_assignment.classroom_id != self.student_enrollment.classroom_id:
                raise ValidationError('Teacher assignment classroom must match student classroom.')

            if self.teacher_assignment.section_id != self.student_enrollment.section_id:
                raise ValidationError('Teacher assignment section must match student section.')

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.student_enrollment.student.full_name} - {self.attendance_date} - {self.status}"
    
class ExamType(models.Model):
    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name='exam_types'
    )

    name = models.CharField(max_length=100)
    code = models.CharField(max_length=50)

    max_score = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=100
    )

    weight_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0
    )

    is_active = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['school', 'code'],
                name='unique_exam_type_code_per_school'
            )
        ]

    def __str__(self):
        return self.name

class Exam(models.Model):
    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('closed', 'Closed'),
        ('cancelled', 'Cancelled'),
    )

    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name='exams'
    )

    academic_year = models.ForeignKey(
        AcademicYear,
        on_delete=models.CASCADE,
        related_name='exams'
    )

    academic_term = models.ForeignKey(
        AcademicTerm,
        on_delete=models.CASCADE,
        related_name='exams'
    )

    teacher_assignment = models.ForeignKey(
        TeacherAssignment,
        on_delete=models.CASCADE,
        related_name='exams'
    )

    exam_type = models.ForeignKey(
        ExamType,
        on_delete=models.CASCADE,
        related_name='exams'
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_exams'
    )

    title = models.CharField(max_length=200)

    exam_date = models.DateField()

    total_marks = models.DecimalField(
        max_digits=6,
        decimal_places=2
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft'
    )

    notes = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=[
                    'academic_term',
                    'teacher_assignment',
                    'exam_type',
                    'title',
                ],
                name='unique_exam_per_assignment_type_title'
            )
        ]

    def clean(self):
        if self.academic_year.school_id != self.school_id:
            raise ValidationError('Academic year must belong to the exam school.')

        if self.academic_term.school_id != self.school_id:
            raise ValidationError('Academic term must belong to the exam school.')

        if self.academic_term.academic_year_id != self.academic_year_id:
            raise ValidationError('Academic term must match academic year.')

        if self.teacher_assignment.school_id != self.school_id:
            raise ValidationError('Teacher assignment school must match exam school.')

        if self.teacher_assignment.academic_year_id != self.academic_year_id:
            raise ValidationError('Teacher assignment academic year must match exam academic year.')

        if self.exam_type.school_id != self.school_id:
            raise ValidationError('Exam type school must match exam school.')

        if self.total_marks <= 0:
            raise ValidationError('Total marks must be greater than zero.')

        if self.total_marks > self.exam_type.max_score:
            raise ValidationError('Total marks cannot exceed exam type max score.')

        if not (self.academic_term.start_date <= self.exam_date <= self.academic_term.end_date):
            raise ValidationError('Exam date must fall within the academic term dates.')

        if self.created_by_id and self.created_by.role != 'super_admin':
            memberships = SchoolMembership.objects.filter(
                user_id=self.created_by_id, role__in=('school_admin', 'teacher'),
            )
            if (
                memberships.exists()
                and not memberships.filter(school_id=self.school_id, status='active').exists()
            ) or (not memberships.exists() and self.created_by.school_id != self.school_id):
                raise ValidationError('Exam creator must belong to the exam school.')

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.title} - {self.teacher_assignment}"

class ExamResult(models.Model):
    STATUS_CHOICES = (
        ('not_graded', 'Not Graded'),
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('excused', 'Excused'),
        ('exempted', 'Exempted'),
    )
    WORKFLOW_CHOICES = (
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )

    exam = models.ForeignKey(
        Exam,
        on_delete=models.CASCADE,
        related_name='results'
    )

    student_enrollment = models.ForeignKey(
        StudentEnrollment,
        on_delete=models.CASCADE,
        related_name='exam_results'
    )

    score = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        blank=True,
        null=True
    )

    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default='not_graded'
    )

    workflow_status = models.CharField(
        max_length=20,
        choices=WORKFLOW_CHOICES,
        default='draft'
    )

    approval_reason = models.TextField(blank=True, null=True)

    is_published = models.BooleanField(default=False)
    published_at = models.DateTimeField(blank=True, null=True)
    published_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='published_exam_results'
    )

    remarks = models.TextField(blank=True, null=True)
    graded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='graded_exam_results'
    )

    graded_at = models.DateTimeField(blank=True, null=True)

    approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='approved_exam_results'
    )

    approved_at = models.DateTimeField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['exam', 'student_enrollment'],
                name='unique_exam_result_per_student'
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(is_published=False)
                    | models.Q(
                        workflow_status='approved',
                        published_by__isnull=False,
                        published_at__isnull=False,
                    )
                ),
                name='published_result_requires_approval_metadata',
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(is_published=True)
                    | models.Q(
                        published_by__isnull=True,
                        published_at__isnull=True,
                    )
                ),
                name='unpublished_result_clears_metadata',
            ),
        ]

    def clean(self):
        if self.exam.academic_year_id != self.student_enrollment.academic_year_id:
            raise ValidationError('Exam academic year must match student enrollment academic year.')

        if self.exam.school_id != self.student_enrollment.school_id:
            raise ValidationError('Exam school must match student enrollment school.')

        if self.status == 'present' and self.score is None:
            raise ValidationError('Score is required when student is present.')

        if self.status in ['absent', 'excused', 'exempted'] and self.score is not None:
            raise ValidationError('Score must be empty when student is absent, excused, or exempted.')

        if self.score is not None and self.score < 0:
            raise ValidationError('Score cannot be negative.')

        if self.score is not None and self.score > self.exam.total_marks:
            raise ValidationError('Score cannot exceed exam total marks.')

        assignment = self.exam.teacher_assignment
        if assignment.classroom_id != self.student_enrollment.classroom_id:
            raise ValidationError('Student classroom must match the exam classroom.')
        if assignment.section_id != self.student_enrollment.section_id:
            raise ValidationError('Student section must match the exam section.')

        for user, label in ((self.graded_by, 'Grader'), (self.approved_by, 'Approver')):
            if user and user.role != 'super_admin' and user.school_id != self.exam.school_id:
                raise ValidationError(f'{label} must belong to the exam school.')

        if self.approved_by and self.status == 'not_graded':
            raise ValidationError('Cannot approve a result that is not graded.')

        if self.approved_by and self.approved_by.role not in ('super_admin', 'school_admin'):
            raise ValidationError('Only school administrators can approve results.')

        if self.workflow_status == 'approved' and not self.approved_by:
            raise ValidationError('Approved results require an approver.')

        if self.workflow_status != 'approved' and self.approved_by:
            raise ValidationError('Only approved results can have an approver.')

        if self.is_published:
            if self.workflow_status != 'approved':
                raise ValidationError('Only approved results can be published.')
            if not self.published_by or not self.published_at:
                raise ValidationError('Published results require publisher and timestamp.')
            if self.published_by.role not in ('super_admin', 'school_admin'):
                raise ValidationError('Only school administrators can publish results.')
            if (
                self.published_by.role == 'school_admin'
                and self.published_by.school_id != self.exam.school_id
            ):
                raise ValidationError('Publisher school must match the exam school.')
        elif self.published_by or self.published_at:
            raise ValidationError('Unpublished results cannot retain publication metadata.')
    def save(self, *args, **kwargs):
        self.full_clean()

        if self.status == 'present' and self.score is not None:
            if not self.graded_at:
                self.graded_at = timezone.now()
        else:
            self.graded_at = None

        if self.approved_by:
            if not self.approved_at:
                self.approved_at = timezone.now()
        else:
            self.approved_at = None

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.exam.title} - {self.student_enrollment.student.full_name}"


class ExamResultLog(models.Model):
    ACTION_CHOICES = (
        ('create', 'Create'),
        ('update', 'Update'),
        ('submit', 'Submit'),
        ('approve', 'Approve'),
        ('reject', 'Reject'),
        ('reopen', 'Reopen'),
        ('publish', 'Publish'),
        ('unpublish', 'Unpublish'),
    )

    exam_result = models.ForeignKey(
        ExamResult,
        on_delete=models.CASCADE,
        related_name='logs'
    )

    old_score = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        blank=True,
        null=True
    )

    new_score = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        blank=True,
        null=True
    )

    old_status = models.CharField(
        max_length=30,
        choices=ExamResult.STATUS_CHOICES,
        blank=True,
        null=True
    )

    new_status = models.CharField(
        max_length=30,
        choices=ExamResult.STATUS_CHOICES,
        blank=True,
        null=True
    )

    old_workflow_status = models.CharField(
        max_length=20,
        choices=ExamResult.WORKFLOW_CHOICES,
        blank=True,
        null=True
    )

    new_workflow_status = models.CharField(
        max_length=20,
        choices=ExamResult.WORKFLOW_CHOICES,
        blank=True,
        null=True
    )

    old_approval_reason = models.TextField(blank=True, null=True)
    new_approval_reason = models.TextField(blank=True, null=True)

    old_is_published = models.BooleanField(blank=True, null=True)
    new_is_published = models.BooleanField(blank=True, null=True)
    published_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='published_exam_result_logs'
    )

    action = models.CharField(
        max_length=20,
        choices=ACTION_CHOICES,
        default='update'
    )

    changed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='exam_result_logs'
    )

    reason = models.TextField(
        blank=True,
        null=True
    )

    request_id = models.CharField(max_length=100, blank=True, null=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.CharField(max_length=512, blank=True, null=True)

    changed_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        ordering = ['-changed_at']

    def __str__(self):
        return f"{self.exam_result} - {self.changed_at}"


def _attachment_path(school_id, kind, owner_id, filename):
    extension = os.path.splitext(filename)[1].lower()[:16]
    return f"schools/{school_id}/{kind}/{owner_id}/{uuid.uuid4().hex}{extension}"


def homework_attachment_upload_to(instance, filename):
    return _attachment_path(instance.homework.school_id, 'homework', instance.homework_id, filename)


def submission_attachment_upload_to(instance, filename):
    return _attachment_path(
        instance.submission.homework.school_id,
        'homework-submissions',
        instance.submission_id,
        filename,
    )


class Homework(models.Model):
    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('closed', 'Closed'),
    )

    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='homework')
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, related_name='homework')
    academic_term = models.ForeignKey(AcademicTerm, on_delete=models.CASCADE, related_name='homework')
    teacher_assignment = models.ForeignKey(
        TeacherAssignment, on_delete=models.CASCADE, related_name='homework',
    )
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    publish_at = models.DateTimeField(blank=True, null=True)
    published_at = models.DateTimeField(blank=True, null=True)
    due_date = models.DateTimeField()
    max_grade = models.DecimalField(max_digits=7, decimal_places=2, blank=True, null=True)
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, blank=True, null=True, related_name='created_homework',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('-created_at', '-id')
        constraints = [
            models.CheckConstraint(
                condition=models.Q(max_grade__isnull=True) | models.Q(max_grade__gte=0),
                name='homework_max_grade_nonnegative',
            ),
            models.CheckConstraint(
                condition=models.Q(publish_at__isnull=True) | models.Q(due_date__gte=models.F('publish_at')),
                name='homework_due_after_scheduled_publish',
            ),
            models.CheckConstraint(
                condition=models.Q(published_at__isnull=True) | models.Q(due_date__gte=models.F('published_at')),
                name='homework_due_after_actual_publish',
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(status='draft', published_at__isnull=True)
                    | models.Q(status__in=('published', 'closed'), published_at__isnull=False)
                ),
                name='homework_status_publication_metadata',
            ),
        ]

    def clean(self):
        assignment = self.teacher_assignment
        if (
            assignment.school_id != self.school_id
            or assignment.academic_year_id != self.academic_year_id
            or self.academic_term.school_id != self.school_id
            or self.academic_term.academic_year_id != self.academic_year_id
        ):
            raise ValidationError('Invalid homework relationships.')
        if self.publish_at and self.due_date < self.publish_at:
            raise ValidationError('Due date cannot precede publish time.')
        if self.published_at and self.due_date < self.published_at:
            raise ValidationError('Due date cannot precede publication time.')
        if self.max_grade is not None and self.max_grade < 0:
            raise ValidationError('Maximum grade cannot be negative.')
        if self.created_by_id and self.created_by.role != 'super_admin':
            memberships = SchoolMembership.objects.filter(
                user_id=self.created_by_id, role__in=('school_admin', 'teacher'),
            )
            if (
                memberships.exists()
                and not memberships.filter(school_id=self.school_id, status='active').exists()
            ) or (not memberships.exists() and self.created_by.school_id != self.school_id):
                raise ValidationError('Homework creator must belong to its school.')

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class HomeworkAttachment(models.Model):
    homework = models.ForeignKey(Homework, on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(upload_to=homework_attachment_upload_to)
    original_name = models.CharField(max_length=255)
    content_type = models.CharField(max_length=150)
    file_size = models.BigIntegerField()
    uploaded_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, blank=True, null=True,
        related_name='uploaded_homework_attachments',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('created_at', 'id')
        constraints = [models.CheckConstraint(
            condition=models.Q(file_size__gte=0), name='homework_attachment_size_nonnegative',
        )]

    def __str__(self):
        return self.original_name


class HomeworkSubmission(models.Model):
    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('graded', 'Graded'),
        ('returned', 'Returned'),
    )

    homework = models.ForeignKey(Homework, on_delete=models.CASCADE, related_name='submissions')
    student_enrollment = models.ForeignKey(
        StudentEnrollment, on_delete=models.CASCADE, related_name='homework_submissions',
    )
    answer = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    submitted_at = models.DateTimeField(blank=True, null=True)
    grade = models.DecimalField(max_digits=7, decimal_places=2, blank=True, null=True)
    teacher_note = models.TextField(blank=True)
    graded_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, blank=True, null=True,
        related_name='graded_homework_submissions',
    )
    graded_at = models.DateTimeField(blank=True, null=True)
    returned_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('-submitted_at', '-created_at', '-id')
        constraints = [
            models.UniqueConstraint(
                fields=('homework', 'student_enrollment'),
                name='unique_homework_submission_per_enrollment',
            ),
            models.CheckConstraint(
                condition=models.Q(grade__isnull=True) | models.Q(grade__gte=0),
                name='homework_submission_grade_nonnegative',
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(status='graded', grade__isnull=False, graded_at__isnull=False)
                    | ~models.Q(status='graded')
                ),
                name='graded_submission_requires_metadata',
            ),
        ]

    @property
    def is_late(self):
        return bool(self.submitted_at and self.submitted_at > self.homework.due_date)

    def clean(self):
        assignment = self.homework.teacher_assignment
        enrollment = self.student_enrollment
        if (
            enrollment.school_id != self.homework.school_id
            or enrollment.academic_year_id != self.homework.academic_year_id
            or enrollment.classroom_id != assignment.classroom_id
            or enrollment.section_id != assignment.section_id
        ):
            raise ValidationError('Invalid homework submission relationships.')
        if self.grade is not None:
            if self.homework.max_grade is None:
                raise ValidationError('This homework is not graded.')
            if self.grade < 0 or self.grade > self.homework.max_grade:
                raise ValidationError('Grade is outside the allowed range.')

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.homework} - {self.student_enrollment.student}'


class HomeworkSubmissionAttachment(models.Model):
    submission = models.ForeignKey(
        HomeworkSubmission, on_delete=models.CASCADE, related_name='attachments',
    )
    file = models.FileField(upload_to=submission_attachment_upload_to)
    original_name = models.CharField(max_length=255)
    content_type = models.CharField(max_length=150)
    file_size = models.BigIntegerField()
    uploaded_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, blank=True, null=True,
        related_name='uploaded_submission_attachments',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('created_at', 'id')
        constraints = [models.CheckConstraint(
            condition=models.Q(file_size__gte=0), name='submission_attachment_size_nonnegative',
        )]

    def __str__(self):
        return self.original_name


class HomeworkActionLog(models.Model):
    school = models.ForeignKey(
        School, on_delete=models.CASCADE, related_name='homework_action_logs',
    )
    actor = models.ForeignKey(
        User, on_delete=models.SET_NULL, blank=True, null=True,
        related_name='homework_action_logs',
    )
    action = models.CharField(max_length=50)
    entity_type = models.CharField(max_length=50)
    entity_id = models.PositiveBigIntegerField()
    old_data = models.JSONField(default=dict, blank=True)
    new_data = models.JSONField(default=dict, blank=True)
    reason = models.TextField(blank=True)
    request_id = models.CharField(max_length=100, blank=True, null=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.CharField(max_length=512, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-created_at', '-id')
        indexes = [models.Index(fields=('school', '-created_at'), name='hw_audit_school_time_idx')]

    def __str__(self):
        return f'{self.entity_type}:{self.entity_id} {self.action}'
class Notification(models.Model):
    TYPE_CHOICES = (
        ('homework_published', 'Homework published'), ('homework_graded', 'Homework graded'),
        ('homework_returned', 'Homework returned'), ('result_published', 'Result published'),
        ('message_received', 'Message received'), ('school_reply', 'School reply'),
        ('school_support_created', 'School support created'), ('announcement_published', 'Announcement published'), ('system', 'System'),
    )
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='notifications')
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    recipient_membership = models.ForeignKey(SchoolMembership, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=40, choices=TYPE_CHOICES)
    title = models.CharField(max_length=200)
    body = models.TextField(blank=True)
    action_url = models.CharField(max_length=300, blank=True)
    payload = models.JSONField(default=dict, blank=True)
    source_type = models.CharField(max_length=50, blank=True)
    source_id = models.PositiveBigIntegerField(blank=True, null=True)
    deduplication_key = models.CharField(max_length=255, blank=True)
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('-created_at', '-id')
        indexes = [
            models.Index(fields=('recipient_membership', 'is_read', '-created_at'), name='notif_member_read_time_idx'),
            models.Index(fields=('school', 'notification_type', '-created_at'), name='notif_school_type_time_idx'),
        ]
        constraints = [
            models.UniqueConstraint(fields=('recipient_membership', 'deduplication_key'), condition=~models.Q(deduplication_key=''), name='unique_notification_dedup_key'),
            models.CheckConstraint(condition=models.Q(is_read=False, read_at__isnull=True) | models.Q(is_read=True, read_at__isnull=False), name='notification_read_metadata_consistent'),
        ]

    def clean(self):
        if self.recipient_membership_id:
            if self.recipient_id != self.recipient_membership.user_id:
                raise ValidationError('Notification recipient must match membership user.')
            if self.school_id != self.recipient_membership.school_id:
                raise ValidationError('Notification school must match membership school.')
        if self.is_read != bool(self.read_at):
            raise ValidationError('Notification read metadata is inconsistent.')


class Conversation(models.Model):
    TYPE_CHOICES = (
        ('teacher_student', 'Teacher and student'), ('teacher_parent', 'Teacher and parent'),
        ('homework_discussion', 'Homework discussion'), ('school_support', 'School support'),
    )
    STATUS_CHOICES = (('open', 'Open'), ('in_progress', 'In progress'), ('resolved', 'Resolved'), ('closed', 'Closed'))
    RELATED_TYPE_CHOICES = (('', 'None'), ('homework', 'Homework'), ('homework_submission', 'Homework submission'), ('subject', 'Subject'), ('general', 'General'), ('student', 'Student'))
    CATEGORY_CHOICES = (('', 'None'), ('academic_inquiry', 'Academic inquiry'), ('absence_excuse', 'Absence excuse'), ('profile_update', 'Profile update'), ('technical_issue', 'Technical issue'), ('complaint', 'Complaint'), ('other', 'Other'))
    PRIORITY_CHOICES = (('low', 'Low'), ('normal', 'Normal'), ('high', 'High'))
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='conversations')
    conversation_type = models.CharField(max_length=40, choices=TYPE_CHOICES)
    subject = models.CharField(max_length=200)
    created_by_membership = models.ForeignKey(SchoolMembership, on_delete=models.PROTECT, related_name='created_conversations')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    related_type = models.CharField(max_length=40, choices=RELATED_TYPE_CHOICES, blank=True)
    related_id = models.PositiveBigIntegerField(blank=True, null=True)
    assigned_to_membership = models.ForeignKey(SchoolMembership, on_delete=models.SET_NULL, blank=True, null=True, related_name='assigned_conversations')
    category = models.CharField(max_length=40, choices=CATEGORY_CHOICES, blank=True)
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='normal')
    resolution_note = models.TextField(blank=True)
    resolved_at = models.DateTimeField(blank=True, null=True)
    closed_at = models.DateTimeField(blank=True, null=True)
    last_message_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('-last_message_at', '-created_at', '-id')
        indexes = [models.Index(fields=('school', 'conversation_type', 'status', '-last_message_at'), name='conv_school_type_state_idx')]
        constraints = [
            models.CheckConstraint(
                condition=(
                    models.Q(related_type='', related_id__isnull=True)
                    | models.Q(related_type='general', related_id__isnull=True)
                    | (~models.Q(related_type__in=('', 'general')) & models.Q(related_id__isnull=False))
                ), name='conversation_related_metadata_consistent',
            ),
            models.CheckConstraint(
                condition=~models.Q(conversation_type='school_support') | ~models.Q(category=''),
                name='school_support_category_required',
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(status='resolved', resolved_at__isnull=False, closed_at__isnull=True)
                    | models.Q(status='closed', resolved_at__isnull=True, closed_at__isnull=False)
                    | models.Q(status__in=('open', 'in_progress'), resolved_at__isnull=True, closed_at__isnull=True)
                ), name='conversation_status_timestamps_consistent',
            ),
        ]

    def clean(self):
        if self.created_by_membership_id and self.created_by_membership.school_id != self.school_id:
            raise ValidationError('Conversation creator membership must belong to its school.')
        if self.assigned_to_membership_id and self.assigned_to_membership.school_id != self.school_id:
            raise ValidationError('Conversation assignee membership must belong to its school.')


class ConversationParticipant(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='participants')
    membership = models.ForeignKey(SchoolMembership, on_delete=models.CASCADE, related_name='conversation_participations')
    participant_role = models.CharField(max_length=50)
    can_reply = models.BooleanField(default=True)
    last_read_at = models.DateTimeField(blank=True, null=True)
    joined_at = models.DateTimeField(auto_now_add=True)
    left_at = models.DateTimeField(blank=True, null=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=('conversation', 'membership'), name='unique_conversation_membership'),
            models.CheckConstraint(
                condition=(models.Q(is_active=True, left_at__isnull=True) | models.Q(is_active=False)),
                name='active_participant_has_not_left',
            ),
        ]
        indexes = [models.Index(fields=('membership', 'is_active', '-joined_at'), name='conv_part_member_active_idx')]

    def clean(self):
        if self.conversation_id and self.membership_id and self.conversation.school_id != self.membership.school_id:
            raise ValidationError('Participant membership must belong to conversation school.')


class Message(models.Model):
    TYPE_CHOICES = (('text', 'Text'), ('system', 'System'))
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender_membership = models.ForeignKey(SchoolMembership, on_delete=models.PROTECT, related_name='sent_messages')
    body = models.TextField(blank=True)
    reply_to = models.ForeignKey('self', on_delete=models.SET_NULL, blank=True, null=True, related_name='replies')
    message_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='text')
    created_at = models.DateTimeField(auto_now_add=True)
    edited_at = models.DateTimeField(blank=True, null=True)
    deleted_at = models.DateTimeField(blank=True, null=True)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        ordering = ('created_at', 'id')
        indexes = [models.Index(fields=('conversation', 'created_at', 'id'), name='message_conv_time_idx')]
        constraints = [models.CheckConstraint(
            condition=(
                models.Q(is_deleted=False, deleted_at__isnull=True)
                | models.Q(is_deleted=True, deleted_at__isnull=False)
            ), name='message_deleted_metadata_consistent',
        )]

    def clean(self):
        if self.sender_membership_id and self.conversation_id:
            if self.sender_membership.school_id != self.conversation.school_id:
                raise ValidationError('Message sender must belong to conversation school.')
            if not ConversationParticipant.objects.filter(conversation_id=self.conversation_id, membership_id=self.sender_membership_id, is_active=True, can_reply=True, left_at__isnull=True).exists():
                raise ValidationError('Message sender is not an active participant.')
        if self.reply_to_id and self.reply_to.conversation_id != self.conversation_id:
            raise ValidationError('Reply target must belong to the same conversation.')
        if not self.body.strip() and not self.pk:
            raise ValidationError('Message body is required before attachments can be added.')


def message_attachment_upload_to(instance, filename):
    return _attachment_path(instance.message.conversation.school_id, 'messages', instance.message_id, filename)


class MessageAttachment(models.Model):
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(upload_to=message_attachment_upload_to)
    original_name = models.CharField(max_length=255)
    content_type = models.CharField(max_length=150)
    file_size = models.BigIntegerField()
    uploaded_by_membership = models.ForeignKey(SchoolMembership, on_delete=models.PROTECT, related_name='uploaded_message_attachments')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('created_at', 'id')
        constraints = [models.CheckConstraint(condition=models.Q(file_size__gt=0), name='message_attachment_size_positive')]

    def clean(self):
        if self.uploaded_by_membership_id and self.message_id and self.uploaded_by_membership.school_id != self.message.conversation.school_id:
            raise ValidationError('Attachment uploader must belong to conversation school.')

def announcement_attachment_upload_to(instance, filename):
    return _attachment_path(instance.announcement.school_id, 'announcements', instance.announcement_id, filename)


class Announcement(models.Model):
    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('closed', 'Closed'),
        ('archived', 'Archived'),
    )
    PRIORITY_CHOICES = (
        ('normal', 'Normal'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    )
    AUDIENCE_CHOICES = (
        ('school', 'Entire school'),
        ('roles', 'Selected roles'),
        ('classroom', 'Classroom'),
        ('section', 'Section'),
        ('teacher_assignment', 'Teacher assignment'),
        ('students', 'Selected students'),
    )

    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='announcements')
    academic_year = models.ForeignKey(
        AcademicYear, on_delete=models.SET_NULL, blank=True, null=True,
        related_name='announcements',
    )
    title = models.CharField(max_length=200)
    body = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='normal')
    audience_type = models.CharField(max_length=30, choices=AUDIENCE_CHOICES, default='school')
    target_roles = models.JSONField(default=list, blank=True)
    classroom = models.ForeignKey(
        Classroom, on_delete=models.SET_NULL, blank=True, null=True,
        related_name='announcements',
    )
    section = models.ForeignKey(
        Section, on_delete=models.SET_NULL, blank=True, null=True,
        related_name='announcements',
    )
    teacher_assignment = models.ForeignKey(
        TeacherAssignment, on_delete=models.SET_NULL, blank=True, null=True,
        related_name='announcements',
    )
    target_students = models.ManyToManyField(Student, blank=True, related_name='targeted_announcements')
    include_parents = models.BooleanField(default=False)
    allow_inquiry = models.BooleanField(default=True)
    created_by_membership = models.ForeignKey(
        SchoolMembership, on_delete=models.PROTECT, related_name='created_announcements',
    )
    published_by_membership = models.ForeignKey(
        SchoolMembership, on_delete=models.SET_NULL, blank=True, null=True,
        related_name='published_announcements',
    )
    published_at = models.DateTimeField(blank=True, null=True)
    closed_at = models.DateTimeField(blank=True, null=True)
    archived_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('-published_at', '-created_at', '-id')
        indexes = [
            models.Index(fields=('school', 'status', '-published_at'), name='ann_school_status_time_idx'),
            models.Index(fields=('school', 'priority', '-created_at'), name='ann_school_priority_idx'),
        ]
        constraints = [
            models.CheckConstraint(
                condition=(
                    models.Q(status='draft', published_at__isnull=True, closed_at__isnull=True, archived_at__isnull=True)
                    | models.Q(status='published', published_at__isnull=False, closed_at__isnull=True, archived_at__isnull=True)
                    | models.Q(status='closed', published_at__isnull=False, closed_at__isnull=False, archived_at__isnull=True)
                    | models.Q(status='archived', archived_at__isnull=False)
                ),
                name='announcement_status_metadata_consistent',
            ),
        ]

    def clean(self):
        if self.created_by_membership_id and self.created_by_membership.school_id != self.school_id:
            raise ValidationError('Announcement creator must belong to the announcement school.')
        if self.published_by_membership_id and self.published_by_membership.school_id != self.school_id:
            raise ValidationError('Announcement publisher must belong to the announcement school.')
        if self.academic_year_id and self.academic_year.school_id != self.school_id:
            raise ValidationError('Announcement academic year must belong to the school.')
        if self.classroom_id and (
            self.classroom.school_id != self.school_id
            or not self.classroom.is_active
            or (self.academic_year_id and self.classroom.academic_year_id != self.academic_year_id)
        ):
            raise ValidationError('Announcement classroom is invalid.')
        if self.section_id and (
            self.section.school_id != self.school_id
            or not self.section.is_active
            or (self.classroom_id and self.section.classroom_id != self.classroom_id)
            or (self.academic_year_id and self.section.academic_year_id != self.academic_year_id)
        ):
            raise ValidationError('Announcement section is invalid.')
        if self.teacher_assignment_id and (
            self.teacher_assignment.school_id != self.school_id
            or not self.teacher_assignment.is_current
            or (self.academic_year_id and self.teacher_assignment.academic_year_id != self.academic_year_id)
        ):
            raise ValidationError('Announcement teacher assignment is invalid.')
        if self.audience_type != 'roles' and self.target_roles:
            raise ValidationError('Target roles are allowed only for role targeting.')
        if self.audience_type not in ('classroom', 'section') and self.classroom_id:
            raise ValidationError('Classroom is not valid for this audience type.')
        if self.audience_type != 'section' and self.section_id:
            raise ValidationError('Section is not valid for this audience type.')
        if self.audience_type != 'teacher_assignment' and self.teacher_assignment_id:
            raise ValidationError('Teacher assignment is not valid for this audience type.')
        if self.audience_type in ('school', 'roles') and self.include_parents:
            raise ValidationError('Parent expansion is not valid for this audience type.')
        valid_roles = {choice[0] for choice in User.ROLE_CHOICES} - {'super_admin'}
        if not isinstance(self.target_roles, list) or any(role not in valid_roles for role in self.target_roles):
            raise ValidationError('Announcement target roles are invalid.')
        if self.audience_type == 'roles' and not self.target_roles:
            raise ValidationError('At least one target role is required.')
        if self.audience_type == 'classroom' and not self.classroom_id:
            raise ValidationError('A classroom is required for this audience.')
        if self.audience_type == 'section' and (not self.classroom_id or not self.section_id):
            raise ValidationError('A classroom and section are required for this audience.')
        if self.audience_type == 'teacher_assignment' and not self.teacher_assignment_id:
            raise ValidationError('A teacher assignment is required for this audience.')

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class AnnouncementAttachment(models.Model):
    announcement = models.ForeignKey(Announcement, on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(upload_to=announcement_attachment_upload_to)
    original_name = models.CharField(max_length=255)
    content_type = models.CharField(max_length=150)
    file_size = models.BigIntegerField()
    uploaded_by_membership = models.ForeignKey(
        SchoolMembership, on_delete=models.PROTECT, related_name='uploaded_announcement_attachments',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('created_at', 'id')
        constraints = [models.CheckConstraint(
            condition=models.Q(file_size__gt=0), name='announcement_attachment_size_positive',
        )]

    def clean(self):
        if self.uploaded_by_membership_id and self.announcement_id:
            if self.uploaded_by_membership.school_id != self.announcement.school_id:
                raise ValidationError('Attachment uploader must belong to announcement school.')

    def __str__(self):
        return self.original_name


class AnnouncementReceipt(models.Model):
    announcement = models.ForeignKey(Announcement, on_delete=models.CASCADE, related_name='receipts')
    recipient_membership = models.ForeignKey(
        SchoolMembership, on_delete=models.CASCADE, related_name='announcement_receipts',
    )
    delivered_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ('-delivered_at', '-id')
        constraints = [models.UniqueConstraint(
            fields=('announcement', 'recipient_membership'),
            name='unique_announcement_receipt_membership',
        )]
        indexes = [models.Index(
            fields=('recipient_membership', 'read_at', '-delivered_at'),
            name='ann_receipt_member_read_idx',
        )]

    @property
    def is_read(self):
        return self.read_at is not None

    def clean(self):
        if self.announcement_id and self.recipient_membership_id:
            if self.announcement.school_id != self.recipient_membership.school_id:
                raise ValidationError('Announcement receipt must remain inside one school.')

    def __str__(self):
        return f'{self.announcement_id}:{self.recipient_membership_id}'
