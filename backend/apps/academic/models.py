from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from apps.accounts.models import User


class AcademicYear(models.Model):
    name = models.CharField(max_length=50)
    start_date = models.DateField()
    end_date = models.DateField()
    start_month = models.IntegerField(
        choices=[(4, 'April'), (6, 'June')],
        default=4,
        help_text="Month when academic year starts"
    )
    end_month = models.IntegerField(
        choices=[(3, 'March'), (5, 'May')],
        default=3,
        help_text="Month when academic year ends"
    )
    is_active = models.BooleanField(default=False)
    school = models.ForeignKey('core.School', on_delete=models.CASCADE, related_name='academic_years', db_constraint=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def clean(self):
        from django.core.exceptions import ValidationError
        from .exceptions import AcademicYearConfigError
        import logging
        from django.db.models import Q
        from django_tenants.utils import schema_context
        from django.db import connection
        
        logger = logging.getLogger('apps.academic')
        errors = {}
        
        # Validate start and end months form valid pairs
        valid_pairs = [(4, 3), (6, 5)]  # April-March or June-May
        if (self.start_month, self.end_month) not in valid_pairs:
            error_msg = f"Invalid academic year configuration: {self.get_start_month_display()}-{self.get_end_month_display()}"
            logger.error(error_msg)
            errors['__all__'] = [error_msg]
            
        # Validate dates align with configured months
        if self.start_date and self.start_date.month != self.start_month:
            error_msg = f"Start date month ({self.start_date.month}) does not match configured start month ({self.start_month})"
            logger.error(error_msg)
            errors['start_date'] = [error_msg]
            
        if self.end_date and self.end_date.month != self.end_month:
            error_msg = f"End date month ({self.end_date.month}) does not match configured end month ({self.end_month})"
            logger.error(error_msg)
            errors['end_date'] = [error_msg]
            
        if errors:
            raise ValidationError(errors)
            
        # Check for overlapping academic years for the same school
        if self.school and self.start_date and self.end_date:
            # Get current schema context
            current_schema = connection.schema_name
            target_schema = self.school.schema_name
            logger.info(f"Current schema: {current_schema}, Target schema: {target_schema}")
            
            try:
                # Only switch context if needed
                if current_schema != target_schema:
                    logger.info(f"Switching to schema: {target_schema}")
                    with schema_context(target_schema):
                        connection.set_tenant(self.school)
                        self._check_overlap()
                else:
                    self._check_overlap()
            except ValidationError as e:
                raise ValidationError(e.message_dict)
                
    def _check_overlap(self):
        """Helper method to check for overlapping academic years."""
        from django.core.exceptions import ValidationError
        import logging
        from django.db.models import Q
        
        logger = logging.getLogger('apps.academic')
        
        overlapping = type(self).objects.filter(
            school=self.school,
            start_date__lte=self.end_date,
            end_date__gte=self.start_date
        ).exclude(pk=self.pk)
        
        if overlapping.exists():
            error_msg = "Academic year dates overlap with existing academic year"
            logger.error(error_msg)
            raise ValidationError({
                '__all__': [error_msg],
                'start_date': ["Start date overlaps with existing academic year"],
                'end_date': ["End date overlaps with existing academic year"]
            })

    def save(self, *args, **kwargs):
        """Ensure validation is run before saving."""
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ["-start_date"]


class Class(models.Model):
    name = models.CharField(max_length=50)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Classes"
        ordering = ["name"]


class Section(models.Model):
    name = models.CharField(max_length=50)
    class_name = models.ForeignKey(
        Class, on_delete=models.CASCADE, related_name="sections"
    )
    teacher = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name="sections"
    )
    academic_year = models.ForeignKey(
        AcademicYear, on_delete=models.CASCADE, related_name="sections"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.class_name} - {self.name}"

    class Meta:
        unique_together = ["name", "class_name", "academic_year"]
        ordering = ["class_name", "name"]


class Subject(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True)
    description = models.TextField(blank=True)
    class_name = models.ForeignKey(
        Class, on_delete=models.CASCADE, related_name="subjects"
    )
    teacher = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name="subjects"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.code})"


class Attendance(models.Model):
    student = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="attendances"
    )
    section = models.ForeignKey(
        Section, on_delete=models.CASCADE, related_name="attendances"
    )
    date = models.DateField()
    is_present = models.BooleanField(default=True)
    remarks = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ["student", "section", "date"]
        ordering = ["-date"]


class Assessment(models.Model):
    name = models.CharField(max_length=100)
    subject = models.ForeignKey(
        Subject, on_delete=models.CASCADE, related_name="assessments"
    )
    section = models.ForeignKey(
        Section, on_delete=models.CASCADE, related_name="assessments"
    )
    date = models.DateField()
    total_marks = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} - {self.subject}"


class AssessmentResult(models.Model):
    assessment = models.ForeignKey(
        Assessment, on_delete=models.CASCADE, related_name="results"
    )
    student = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="assessment_results"
    )
    marks_obtained = models.PositiveIntegerField()
    remarks = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ["assessment", "student"]

    def clean(self):
        if self.marks_obtained > self.assessment.total_marks:
            raise ValueError("Marks obtained cannot be greater than total marks")


class Assignment(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    subject = models.ForeignKey(
        Subject, on_delete=models.CASCADE, related_name="assignments"
    )
    section = models.ForeignKey(
        Section, on_delete=models.CASCADE, related_name="assignments"
    )
    due_date = models.DateTimeField()
    file = models.FileField(upload_to="assignments/", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title


class AssignmentSubmission(models.Model):
    assignment = models.ForeignKey(
        Assignment, on_delete=models.CASCADE, related_name="submissions"
    )
    student = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="assignment_submissions"
    )
    file = models.FileField(upload_to="assignment_submissions/")
    submitted_at = models.DateTimeField(auto_now_add=True)
    remarks = models.TextField(blank=True)
    score = models.PositiveIntegerField(
        null=True, blank=True, validators=[MinValueValidator(0), MaxValueValidator(100)]
    )

    class Meta:
        unique_together = ["assignment", "student"]


class Timetable(models.Model):
    WEEKDAY_CHOICES = [
        (0, "Monday"),
        (1, "Tuesday"),
        (2, "Wednesday"),
        (3, "Thursday"),
        (4, "Friday"),
        (5, "Saturday"),
        (6, "Sunday"),
    ]

    section = models.ForeignKey(
        Section, on_delete=models.CASCADE, related_name="timetable_entries"
    )
    subject = models.ForeignKey(
        Subject, on_delete=models.CASCADE, related_name="timetable_entries"
    )
    weekday = models.IntegerField(choices=WEEKDAY_CHOICES)
    start_time = models.TimeField()
    end_time = models.TimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ["section", "weekday", "start_time"]
        ordering = ["weekday", "start_time"]

    def __str__(self):
        return f"{self.get_weekday_display()} - {self.subject} ({self.start_time} to {self.end_time})"
