from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
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
from .serializers import (
    AcademicYearSerializer,
    ClassSerializer,
    SectionListSerializer,
    SectionCreateSerializer,
    SubjectSerializer,
    AttendanceSerializer,
    AssessmentSerializer,
    AssessmentResultSerializer,
    AssignmentSerializer,
    AssignmentSubmissionSerializer,
    TimetableSerializer,
    StudentProfileSerializer,
    TeacherSerializer,
)
from apps.accounts.models import StudentProfile
from apps.accounts.permissions import IsAdminUser, IsTeacherUser, IsStudentUser

User = get_user_model()


class AcademicYearViewSet(viewsets.ModelViewSet):
    serializer_class = AcademicYearSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name"]
    ordering_fields = ["start_date", "name"]
    ordering = ["-start_date"]

    def get_queryset(self):
        """Filter queryset by current tenant."""
        import logging
        from django.db import connection, transaction
        from django_tenants.utils import schema_context, get_tenant_model

        logger = logging.getLogger("apps.academic")
        tenant = self.request.tenant
        logger.info(f"Getting academic years for tenant: {tenant.name}")

        with schema_context(tenant.schema_name):
            connection.set_tenant(tenant)
            with transaction.atomic():
                try:
                    queryset = AcademicYear.objects.select_related("school").filter(
                        school=tenant
                    )
                    count = queryset.count()
                    logger.info(
                        f"Found {count} academic years in schema {tenant.schema_name}"
                    )
                    return (
                        queryset.all()
                    )  # Materialize the queryset within the schema context
                except Exception as e:
                    logger.error(
                        f"Error getting academic years: {str(e)}", exc_info=True
                    )
                    raise

    def get_permissions(self):
        import logging

        logger = logging.getLogger("apps.academic")
        logger.info(f"Checking permissions for action: {self.action}")
        if self.action in ["create", "update", "partial_update", "destroy"]:
            return [IsAdminUser()]
        return super().get_permissions()

    def perform_create(self, serializer):
        """Create academic year."""
        import logging
        from django.db import connection, transaction
        from django_tenants.utils import schema_context

        logger = logging.getLogger("apps.academic")
        tenant = self.request.tenant
        logger.info(f"Creating academic year for tenant: {tenant.name}")

        with schema_context(tenant.schema_name):
            connection.set_tenant(tenant)
            with transaction.atomic():
                try:
                    instance = serializer.save(school=tenant)
                    logger.info(
                        f"Created academic year {instance.pk} in schema {tenant.schema_name}"
                    )
                except Exception as e:
                    logger.error(f"Error creating academic year: {str(e)}")
                    raise

    def perform_update(self, serializer):
        """Update academic year."""
        import logging
        from django.db import connection, transaction
        from django_tenants.utils import schema_context

        logger = logging.getLogger("apps.academic")
        tenant = self.request.tenant
        logger.info(f"Updating academic year for tenant: {tenant.name}")

        with schema_context(tenant.schema_name):
            connection.set_tenant(tenant)
            with transaction.atomic():
                try:
                    instance = serializer.save()
                    logger.info(
                        f"Updated academic year {instance.pk} in schema {tenant.schema_name}"
                    )
                except Exception as e:
                    logger.error(f"Error updating academic year: {str(e)}")
                    raise

    def perform_destroy(self, instance):
        """Delete academic year."""
        import logging
        from django.db import connection, transaction
        from django_tenants.utils import schema_context

        logger = logging.getLogger("apps.academic")
        tenant = self.request.tenant
        logger.info(f"Deleting academic year {instance.pk} for tenant: {tenant.name}")

        with schema_context(tenant.schema_name):
            connection.set_tenant(tenant)
            with transaction.atomic():
                try:
                    instance.delete()
                    logger.info(
                        f"Deleted academic year {instance.pk} in schema {tenant.schema_name}"
                    )
                except Exception as e:
                    logger.error(f"Error deleting academic year: {str(e)}")
                    raise


class ClassViewSet(viewsets.ModelViewSet):
    queryset = Class.objects.all()
    serializer_class = ClassSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name"]
    ordering_fields = ["name"]
    ordering = ["name"]

    def get_permissions(self):
        if self.action in ["create", "update", "partial_update", "destroy"]:
            return [IsAdminUser()]
        return super().get_permissions()


class SectionViewSet(viewsets.ModelViewSet):
    queryset = Section.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name", "class_name__name"]
    ordering_fields = ["name", "class_name__name"]
    ordering = ["class_name__name", "name"]

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return SectionCreateSerializer
        return SectionListSerializer

    def get_permissions(self):
        if self.action in ["create", "update", "partial_update", "destroy"]:
            return [IsAdminUser()]
        return super().get_permissions()

    def get_queryset(self):
        user = self.request.user
        if user.role == "super_admin":
            return Section.objects.all()
        elif user.role == "school_admin":
            return Section.objects.filter(academic_year__school=user.school)
        elif user.role == "teacher":
            return Section.objects.filter(
                Q(teacher=user) | Q(subjects__teacher=user)
            ).distinct()
        elif user.role == "student":
            return Section.objects.filter(students=user)
        return Section.objects.none()

    @action(detail=True, methods=["post"])
    def add_students(self, request, pk=None):
        section = self.get_object()
        student_ids = request.data.get("student_ids", [])
        students = User.objects.filter(id__in=student_ids, role="student")
        section.students.add(*students)
        return Response({"status": "Students added successfully"})

    @action(detail=True, methods=["post"])
    def remove_students(self, request, pk=None):
        section = self.get_object()
        student_ids = request.data.get("student_ids", [])
        students = User.objects.filter(id__in=student_ids, role="student")
        section.students.remove(*students)
        return Response({"status": "Students removed successfully"})


class SubjectViewSet(viewsets.ModelViewSet):
    queryset = Subject.objects.all()
    serializer_class = SubjectSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name", "code", "class_name__name"]
    ordering_fields = ["name", "code", "class_name__name"]
    ordering = ["class_name__name", "name"]

    def get_permissions(self):
        if self.action in ["create", "update", "partial_update", "destroy"]:
            return [IsAdminUser()]
        return super().get_permissions()

    def get_queryset(self):
        user = self.request.user
        if user.role == "super_admin":
            return Subject.objects.all()
        elif user.role == "school_admin":
            return Subject.objects.filter(class_name__school=user.school)
        elif user.role == "teacher":
            return Subject.objects.filter(teacher=user)
        elif user.role == "student":
            return Subject.objects.filter(class_name__sections__students=user)
        return Subject.objects.none()


class AttendanceViewSet(viewsets.ModelViewSet):
    queryset = Attendance.objects.all()
    serializer_class = AttendanceSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["student__username", "section__name"]
    ordering_fields = ["date", "student__username"]
    ordering = ["-date"]

    def get_permissions(self):
        if self.action in ["create", "update", "partial_update"]:
            return [IsTeacherUser()]
        elif self.action == "destroy":
            return [IsAdminUser()]
        return super().get_permissions()

    def get_queryset(self):
        user = self.request.user
        if user.role == "super_admin":
            return Attendance.objects.all()
        elif user.role == "school_admin":
            return Attendance.objects.filter(section__school=user.school)
        elif user.role == "teacher":
            return Attendance.objects.filter(section__teacher=user)
        elif user.role == "student":
            return Attendance.objects.filter(student=user)
        return Attendance.objects.none()

    @action(detail=False, methods=["post"])
    def bulk_create(self, request):
        serializer = self.get_serializer(data=request.data, many=True)
        serializer.is_valid(raise_exception=True)
        self.perform_bulk_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def perform_bulk_create(self, serializer):
        serializer.save()


class AssessmentViewSet(viewsets.ModelViewSet):
    queryset = Assessment.objects.all()
    serializer_class = AssessmentSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name", "subject__name", "section__name"]
    ordering_fields = ["date", "name"]
    ordering = ["-date"]

    def get_permissions(self):
        if self.action in ["create", "update", "partial_update"]:
            return [IsTeacherUser()]
        elif self.action == "destroy":
            return [IsAdminUser()]
        return super().get_permissions()

    def get_queryset(self):
        user = self.request.user
        if user.role == "super_admin":
            return Assessment.objects.all()
        elif user.role == "school_admin":
            return Assessment.objects.filter(section__school=user.school)
        elif user.role == "teacher":
            return Assessment.objects.filter(
                Q(section__teacher=user) | Q(subject__teacher=user)
            )
        elif user.role == "student":
            return Assessment.objects.filter(section__students=user)
        return Assessment.objects.none()


class AssessmentResultViewSet(viewsets.ModelViewSet):
    queryset = AssessmentResult.objects.all()
    serializer_class = AssessmentResultSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["student__username", "assessment__name"]
    ordering_fields = ["marks_obtained", "student__username"]
    ordering = ["-assessment__date"]

    def get_permissions(self):
        if self.action in ["create", "update", "partial_update"]:
            return [IsTeacherUser()]
        elif self.action == "destroy":
            return [IsAdminUser()]
        return super().get_permissions()

    def get_queryset(self):
        user = self.request.user
        if user.role == "super_admin":
            return AssessmentResult.objects.all()
        elif user.role == "school_admin":
            return AssessmentResult.objects.filter(
                assessment__section__school=user.school
            )
        elif user.role == "teacher":
            return AssessmentResult.objects.filter(
                Q(assessment__section__teacher=user)
                | Q(assessment__subject__teacher=user)
            )
        elif user.role == "student":
            return AssessmentResult.objects.filter(student=user)
        return AssessmentResult.objects.none()

    @action(detail=False, methods=["post"])
    def bulk_create(self, request):
        serializer = self.get_serializer(data=request.data, many=True)
        serializer.is_valid(raise_exception=True)
        self.perform_bulk_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def perform_bulk_create(self, serializer):
        serializer.save()


class AssignmentViewSet(viewsets.ModelViewSet):
    queryset = Assignment.objects.all()
    serializer_class = AssignmentSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["title", "subject__name", "section__name"]
    ordering_fields = ["due_date", "title"]
    ordering = ["-due_date"]

    def get_permissions(self):
        if self.action in ["create", "update", "partial_update"]:
            return [IsTeacherUser()]
        elif self.action == "destroy":
            return [IsAdminUser()]
        return super().get_permissions()

    def get_queryset(self):
        user = self.request.user
        if user.role == "super_admin":
            return Assignment.objects.all()
        elif user.role == "school_admin":
            return Assignment.objects.filter(section__school=user.school)
        elif user.role == "teacher":
            return Assignment.objects.filter(
                Q(section__teacher=user) | Q(subject__teacher=user)
            )
        elif user.role == "student":
            return Assignment.objects.filter(section__students=user)
        return Assignment.objects.none()


class AssignmentSubmissionViewSet(viewsets.ModelViewSet):
    queryset = AssignmentSubmission.objects.all()
    serializer_class = AssignmentSubmissionSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["student__username", "assignment__title"]
    ordering_fields = ["submitted_at", "score"]
    ordering = ["-submitted_at"]

    def get_permissions(self):
        if self.action == "create":
            return [IsStudentUser()]
        elif self.action in ["update", "partial_update"]:
            return [IsTeacherUser()]
        elif self.action == "destroy":
            return [IsAdminUser()]
        return super().get_permissions()

    def get_queryset(self):
        user = self.request.user
        if user.role == "super_admin":
            return AssignmentSubmission.objects.all()
        elif user.role == "school_admin":
            return AssignmentSubmission.objects.filter(
                assignment__section__school=user.school
            )
        elif user.role == "teacher":
            return AssignmentSubmission.objects.filter(
                Q(assignment__section__teacher=user)
                | Q(assignment__subject__teacher=user)
            )
        elif user.role == "student":
            return AssignmentSubmission.objects.filter(student=user)
        return AssignmentSubmission.objects.none()


class TimetableViewSet(viewsets.ModelViewSet):
    queryset = Timetable.objects.all()
    serializer_class = TimetableSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["section__name", "subject__name"]
    ordering_fields = ["weekday", "start_time"]
    ordering = ["weekday", "start_time"]


class TeacherViewSet(viewsets.ModelViewSet):
    """ViewSet for managing teachers with role-based access control and staff limits."""

    serializer_class = TeacherSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["username", "email", "first_name", "last_name"]
    ordering_fields = ["username", "date_joined"]
    ordering = ["username"]

    def get_queryset(self):
        user = self.request.user
        if user.role == "super_admin":
            return User.objects.filter(role="teacher")
        elif user.role == "school_admin":
            return User.objects.filter(role="teacher", school=user.school)
        elif user.role == "teacher":
            # Teachers can only view other teachers in their school
            return User.objects.filter(role="teacher", school=user.school)
        return User.objects.none()

    def get_permissions(self):
        if self.action in ["create", "update", "partial_update", "destroy"]:
            return [IsAdminUser()]
        return super().get_permissions()

    def perform_create(self, serializer):
        """Create teacher with staff limit check."""
        user = self.request.user
        if user.role in ["super_admin", "school_admin"]:
            # Check staff limit for free tier
            teacher_count = User.objects.filter(
                role="teacher", school=user.school
            ).count()
            if teacher_count >= 50:
                raise ValidationError(
                    {
                        "detail": "Free tier limit of 50 staff members reached. Please upgrade your plan."
                    }
                )
            serializer.save(role="teacher", school=user.school)
        else:
            raise ValidationError(
                {"detail": "Only administrators can create teacher accounts."}
            )


class StudentViewSet(viewsets.ModelViewSet):
    """ViewSet for managing students with role-based access control."""

    serializer_class = StudentProfileSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = [
        "user__username",
        "user__first_name",
        "user__last_name",
        "admission_number",
    ]
    ordering_fields = ["user__username", "admission_number", "created_at"]
    ordering = ["admission_number"]

    def get_queryset(self):
        """Get queryset based on user role and enforce free tier limits."""
        user = self.request.user
        if not hasattr(user, "school"):
            return StudentProfile.objects.none()

        queryset = StudentProfile.objects.select_related("user", "user__school").all()

        # Role-based filtering
        if user.role == "super_admin":
            return queryset
        elif user.role == "school_admin":
            # Check free tier limits for school admins on create
            if self.action == "create":
                student_count = StudentProfile.objects.filter(
                    user__school=user.school
                ).count()
                if student_count >= 500:
                    raise ValidationError(
                        {
                            "detail": "Free tier limit of 500 students reached. Please upgrade your plan."
                        }
                    )
            return queryset.filter(user__school=user.school)
        elif user.role == "teacher":
            # Get sections where the user is a teacher
            teacher_sections = Section.objects.filter(
                Q(teacher=user) | Q(subjects__teacher=user)
            ).distinct()
            # Get students in those sections
            return queryset.filter(
                user__section__in=teacher_sections, user__school=user.school
            ).distinct()
        elif user.role == "student":
            # Students can only see their own profile
            return queryset.filter(user=user)

        return StudentProfile.objects.none()

    def get_permissions(self):
        """Ensure proper permissions based on action."""
        if self.action in ["create", "update", "partial_update", "destroy"]:
            return [IsAdminUser()]
        return [IsAuthenticated()]

    def perform_create(self, serializer):
        """Ensure new students are associated with the current school."""
        user = self.request.user
        if user.role in ["super_admin", "school_admin"]:
            if serializer.validated_data.get("user"):
                serializer.validated_data["user"].school = user.school
            serializer.save()
        else:
            raise ValidationError(
                {"detail": "Only administrators can create student profiles."}
            )
