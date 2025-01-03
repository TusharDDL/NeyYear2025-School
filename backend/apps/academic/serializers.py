from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (
    AcademicYear,
    Class,
    Section,
    Subject,
    Attendance,
    Assessment,
    AssessmentResult,
    Assignment,
    AssignmentSubmission,
    Timetable,
)
from apps.accounts.serializers import UserSerializer
from apps.accounts.models import StudentProfile

User = get_user_model()


class AcademicYearSerializer(serializers.ModelSerializer):
    class Meta:
        model = AcademicYear
        fields = [
            "id",
            "name",
            "start_date",
            "end_date",
            "start_month",
            "end_month",
            "is_active",
            "created_at",
            "school",
        ]
        read_only_fields = ["created_at", "school"]

    def validate(self, data):
        """Validate academic year data."""
        import logging
        from django.db import connection
        from django_tenants.utils import schema_context
        from django.core.exceptions import ValidationError as DjangoValidationError
        from rest_framework import serializers
        from apps.academic.models import AcademicYear
        from django.db.models import Q

        logger = logging.getLogger("apps.academic")

        # Get tenant from context
        request = self.context.get("request")
        if not request or not hasattr(request, "tenant"):
            logger.error("Tenant context missing in request")
            raise serializers.ValidationError(
                {"non_field_errors": ["Tenant context is required"]}
            )

        tenant = request.tenant
        logger.info(f"Validating academic year data for tenant: {tenant.name}")

        with schema_context(tenant.schema_name):
            connection.set_tenant(tenant)
            logger.info(f"Schema in context: {connection.schema_name}")

            # Check for overlapping years
            start_date = data.get("start_date")
            end_date = data.get("end_date")

            if not start_date or not end_date:
                raise serializers.ValidationError(
                    {
                        "non_field_errors": ["Start date and end date are required"],
                        "start_date": (
                            ["This field is required"] if not start_date else []
                        ),
                        "end_date": ["This field is required"] if not end_date else [],
                    }
                )

            if start_date >= end_date:
                raise serializers.ValidationError(
                    {
                        "non_field_errors": ["End date must be after start date"],
                        "start_date": ["Start date must be before end date"],
                        "end_date": ["End date must be after start date"],
                    }
                )

            # Build overlap query for strict validation
            overlap_query = Q(
                school=tenant, start_date__lt=end_date, end_date__gt=start_date
            )

            # Exclude current instance if this is an update
            if self.instance:
                overlap_query &= ~Q(pk=self.instance.pk)

            # Check for overlapping academic years within tenant schema
            overlapping_years = AcademicYear.objects.filter(overlap_query)

            if overlapping_years.exists():
                logger.error(
                    f"Overlapping academic year detected in schema {tenant.schema_name}"
                )
                overlapping_year = overlapping_years.first()
                error_msg = (
                    f"Academic year dates overlap with existing academic year: "
                    f"{overlapping_year.name} ({overlapping_year.start_date} to {overlapping_year.end_date})"
                )
                raise serializers.ValidationError(
                    {
                        "non_field_errors": [error_msg],
                        "start_date": [
                            "Start date must not overlap with existing academic years"
                        ],
                        "end_date": [
                            "End date must not overlap with existing academic years"
                        ],
                    }
                )

            # Create a model instance for validation
            instance = AcademicYear(
                name=data.get("name", ""),
                start_date=start_date,
                end_date=end_date,
                start_month=data.get("start_month"),
                end_month=data.get("end_month"),
                school=tenant,
            )

            if self.instance:
                instance.pk = self.instance.pk

            try:
                # Use model's validation
                instance.full_clean()
            except DjangoValidationError as e:
                logger.error(f"Validation error: {str(e)}")
                # Convert Django validation error to DRF validation error
                if hasattr(e, "message_dict"):
                    raise serializers.ValidationError(e.message_dict)
                raise serializers.ValidationError({"non_field_errors": e.messages})

            return data

    def create(self, validated_data):
        """Create academic year with proper tenant context."""
        from django.db import transaction, connection
        from django_tenants.utils import schema_context
        import logging

        logger = logging.getLogger("apps.academic")

        # Get the tenant from the context
        request = self.context.get("request")
        if not request or not hasattr(request, "tenant"):
            logger.error("Tenant context missing in request")
            raise serializers.ValidationError(
                {"non_field_errors": ["Tenant context is required"]}
            )

        tenant = request.tenant
        logger.info(
            f"Creating academic year for tenant: {tenant.name} (schema: {tenant.schema_name})"
        )

        # Create academic year within tenant schema context
        with schema_context(tenant.schema_name):
            connection.set_tenant(tenant)
            logger.info(f"Schema in context: {connection.schema_name}")

            with transaction.atomic():
                try:
                    # Create and save instance
                    instance = AcademicYear(**validated_data)
                    instance.school = tenant
                    instance.save()
                    logger.info(f"Successfully created academic year: {instance.pk}")
                    return instance
                except Exception as e:
                    logger.error(
                        f"Error creating academic year: {str(e)}", exc_info=True
                    )
                    raise serializers.ValidationError({"non_field_errors": [str(e)]})

    def update(self, instance, validated_data):
        """Update academic year with proper tenant context."""
        from django.db import transaction
        from django_tenants.utils import schema_context

        # Get the tenant from the context
        request = self.context.get("request")
        if not request or not hasattr(request, "tenant"):
            raise serializers.ValidationError("Tenant context is required")

        # Update academic year within tenant schema context
        with schema_context(request.tenant.schema_name):
            with transaction.atomic():
                try:
                    for attr, value in validated_data.items():
                        setattr(instance, attr, value)
                    instance.save()
                    return instance
                except Exception as e:
                    raise serializers.ValidationError(
                        f"Error updating academic year: {str(e)}"
                    )


class ClassSerializer(serializers.ModelSerializer):
    class Meta:
        model = Class
        fields = ["id", "name", "description", "created_at"]
        read_only_fields = ["created_at"]


class SectionListSerializer(serializers.ModelSerializer):
    class_name = ClassSerializer(read_only=True)
    teacher = UserSerializer(read_only=True)
    academic_year = AcademicYearSerializer(read_only=True)
    student_count = serializers.SerializerMethodField()

    class Meta:
        model = Section
        fields = [
            "id",
            "name",
            "class_name",
            "teacher",
            "academic_year",
            "student_count",
            "created_at",
        ]
        read_only_fields = ["created_at"]

    def get_student_count(self, obj):
        return obj.students.count()


class SectionCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Section
        fields = ["id", "name", "class_name", "teacher", "academic_year"]


class SubjectSerializer(serializers.ModelSerializer):
    class_name = ClassSerializer(read_only=True)
    teacher = UserSerializer(read_only=True)
    class_name_id = serializers.PrimaryKeyRelatedField(
        queryset=Class.objects.all(), source="class_name", write_only=True
    )
    teacher_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(role="teacher"), source="teacher", write_only=True
    )

    class Meta:
        model = Subject
        fields = [
            "id",
            "name",
            "code",
            "description",
            "class_name",
            "teacher",
            "class_name_id",
            "teacher_id",
            "created_at",
        ]
        read_only_fields = ["created_at"]


class AttendanceSerializer(serializers.ModelSerializer):
    student = UserSerializer(read_only=True)
    section = SectionListSerializer(read_only=True)
    student_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(role="student"), source="student", write_only=True
    )
    section_id = serializers.PrimaryKeyRelatedField(
        queryset=Section.objects.all(), source="section", write_only=True
    )

    class Meta:
        model = Attendance
        fields = [
            "id",
            "student",
            "section",
            "date",
            "is_present",
            "remarks",
            "student_id",
            "section_id",
            "created_at",
        ]
        read_only_fields = ["created_at"]


class AssessmentSerializer(serializers.ModelSerializer):
    subject = SubjectSerializer(read_only=True)
    section = SectionListSerializer(read_only=True)
    subject_id = serializers.PrimaryKeyRelatedField(
        queryset=Subject.objects.all(), source="subject", write_only=True
    )
    section_id = serializers.PrimaryKeyRelatedField(
        queryset=Section.objects.all(), source="section", write_only=True
    )

    class Meta:
        model = Assessment
        fields = [
            "id",
            "name",
            "subject",
            "section",
            "date",
            "total_marks",
            "subject_id",
            "section_id",
            "created_at",
        ]
        read_only_fields = ["created_at"]


class AssessmentResultSerializer(serializers.ModelSerializer):
    assessment = AssessmentSerializer(read_only=True)
    student = UserSerializer(read_only=True)
    assessment_id = serializers.PrimaryKeyRelatedField(
        queryset=Assessment.objects.all(), source="assessment", write_only=True
    )
    student_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(role="student"), source="student", write_only=True
    )

    class Meta:
        model = AssessmentResult
        fields = [
            "id",
            "assessment",
            "student",
            "marks_obtained",
            "remarks",
            "assessment_id",
            "student_id",
            "created_at",
        ]
        read_only_fields = ["created_at"]

    def validate(self, data):
        if data["marks_obtained"] > data["assessment"].total_marks:
            raise serializers.ValidationError(
                "Marks obtained cannot be greater than total marks"
            )
        return data


class AssignmentSerializer(serializers.ModelSerializer):
    subject = SubjectSerializer(read_only=True)
    section = SectionListSerializer(read_only=True)
    subject_id = serializers.PrimaryKeyRelatedField(
        queryset=Subject.objects.all(), source="subject", write_only=True
    )
    section_id = serializers.PrimaryKeyRelatedField(
        queryset=Section.objects.all(), source="section", write_only=True
    )
    submission_count = serializers.SerializerMethodField()

    class Meta:
        model = Assignment
        fields = [
            "id",
            "title",
            "description",
            "subject",
            "section",
            "due_date",
            "file",
            "subject_id",
            "section_id",
            "submission_count",
            "created_at",
        ]
        read_only_fields = ["created_at"]

    def get_submission_count(self, obj):
        return obj.submissions.count()


class AssignmentSubmissionSerializer(serializers.ModelSerializer):
    assignment = AssignmentSerializer(read_only=True)
    student = UserSerializer(read_only=True)
    assignment_id = serializers.PrimaryKeyRelatedField(
        queryset=Assignment.objects.all(), source="assignment", write_only=True
    )
    student_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(role="student"), source="student", write_only=True
    )

    class Meta:
        model = AssignmentSubmission
        fields = [
            "id",
            "assignment",
            "student",
            "file",
            "submitted_at",
            "remarks",
            "score",
            "assignment_id",
            "student_id",
        ]
        read_only_fields = ["submitted_at"]


class TimetableSerializer(serializers.ModelSerializer):
    section = SectionListSerializer(read_only=True)
    subject = SubjectSerializer(read_only=True)
    section_id = serializers.PrimaryKeyRelatedField(
        queryset=Section.objects.all(), source="section", write_only=True
    )
    subject_id = serializers.PrimaryKeyRelatedField(
        queryset=Subject.objects.all(), source="subject", write_only=True
    )

    class Meta:
        model = Timetable
        fields = [
            "id",
            "section",
            "subject",
            "weekday",
            "start_time",
            "end_time",
            "section_id",
            "subject_id",
            "created_at",
        ]
        read_only_fields = ["created_at"]

    def validate(self, data):
        # Check for time slot conflicts
        conflicts = Timetable.objects.filter(
            section=data["section"], weekday=data["weekday"]
        ).exclude(id=self.instance.id if self.instance else None)

        for entry in conflicts:
            if (
                (
                    data["start_time"] >= entry.start_time
                    and data["start_time"] < entry.end_time
                )
                or (
                    data["end_time"] > entry.start_time
                    and data["end_time"] <= entry.end_time
                )
                or (
                    data["start_time"] <= entry.start_time
                    and data["end_time"] >= entry.end_time
                )
            ):
                raise serializers.ValidationError(
                    "This time slot conflicts with another entry"
                )

        if data["start_time"] >= data["end_time"]:
            raise serializers.ValidationError("End time must be after start time")

        return data


class TeacherSerializer(serializers.ModelSerializer):
    """Serializer for teacher users with role-based access control and free tier limits."""

    password = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "date_joined",
            "role",
            "is_active",
            "password",
        ]
        read_only_fields = ["id", "date_joined", "role"]

    def validate(self, data):
        if self.instance and self.instance.role != "teacher":
            raise serializers.ValidationError("User must be a teacher")
        return data

    def create(self, validated_data):
        request = self.context.get("request")
        if not request or not hasattr(request, "tenant"):
            raise serializers.ValidationError("Tenant context is required")

        # Check staff limit for free tier
        current_staff_count = User.objects.filter(role="teacher").count()
        if current_staff_count >= 50:  # Free tier limit
            raise serializers.ValidationError(
                "Free tier schools are limited to 50 staff members. "
                "Please upgrade your plan to add more staff."
            )

        password = validated_data.pop("password")
        user = User.objects.create(role="teacher", **validated_data)
        user.set_password(password)
        user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance


class StudentProfileSerializer(serializers.ModelSerializer):
    """Serializer for student profiles with role-based access control."""

    username = serializers.CharField(source="user.username", read_only=True)
    first_name = serializers.CharField(source="user.first_name", read_only=True)
    last_name = serializers.CharField(source="user.last_name", read_only=True)
    email = serializers.EmailField(source="user.email", read_only=True)
    section_name = serializers.CharField(source="user.section.name", read_only=True)
    class_name = serializers.CharField(
        source="user.section.class_name.name", read_only=True
    )

    class Meta:
        model = StudentProfile
        fields = [
            "id",
            "username",
            "first_name",
            "last_name",
            "email",
            "admission_number",
            "date_of_birth",
            "gender",
            "blood_group",
            "parent_name",
            "parent_phone",
            "parent_email",
            "section_name",
            "class_name",
        ]
        read_only_fields = ["id"]
