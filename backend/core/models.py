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

    def __str__(self):
        return self.username

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
                        last_teacher.employee_code.split('-')[-1]
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
            )
        ]

    def clean(self):
        if self.student.school_id != self.school_id:
            raise ValidationError('Student school must match enrollment school.')

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
        if self.teacher.school_id != self.school_id:
            raise ValidationError('Teacher school must match assignment school.')

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
        if self.academic_term.academic_year_id != self.academic_year_id:
            raise ValidationError('Academic term must match academic year.')

        if self.teacher_assignment.school_id != self.school_id:
            raise ValidationError('Teacher assignment school must match exam school.')

        if self.teacher_assignment.academic_year_id != self.academic_year_id:
            raise ValidationError('Teacher assignment academic year must match exam academic year.')

        if self.exam_type.school_id != self.school_id:
            raise ValidationError('Exam type school must match exam school.')

        if self.total_marks > self.exam_type.max_score:
            raise ValidationError('Total marks cannot exceed exam type max score.')

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
            )
        ]

    def clean(self):
        if self.exam.academic_year_id != self.student_enrollment.academic_year_id:
            raise ValidationError('Exam academic year must match student enrollment academic year.')

        if self.exam.school_id != self.student_enrollment.school_id:
            raise ValidationError('Exam school must match student enrollment school.')

        if self.status == 'present' and self.score is None:
            raise ValidationError('Score is required when student is present.')

        if self.status in ['absent', 'excused', 'exempted'] and self.score:
            raise ValidationError('Score must be empty when student is absent, excused, or exempted.')

        if self.score is not None and self.score > self.exam.total_marks:
            raise ValidationError('Score cannot exceed exam total marks.')

        if self.approved_by and self.status == 'not_graded':
            raise ValidationError('Cannot approve a result that is not graded.')

    def save(self, *args, **kwargs):
        self.full_clean()

        if self.status == 'present' and self.score is not None and not self.graded_at:
            self.graded_at = timezone.now()

        if self.approved_by and not self.approved_at:
            self.approved_at = timezone.now()

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.exam.title} - {self.student_enrollment.student.full_name}"


class ExamResultLog(models.Model):
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

    changed_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        ordering = ['-changed_at']

    def __str__(self):
        return f"{self.exam_result} - {self.changed_at}"