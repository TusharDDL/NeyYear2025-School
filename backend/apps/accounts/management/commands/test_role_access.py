from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.test import Client
from django.db import connection
from django_tenants.utils import schema_context
from apps.accounts.models import StudentProfile, TeacherProfile, User
from apps.core.models import School, Domain
from rest_framework_simplejwt.tokens import RefreshToken
import json
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Test role-based access control and free tier limits"

    def add_arguments(self, parser):
        parser.add_argument(
            "--create-users",
            action="store_true",
            help="Create test users if they don't exist",
        )

    def setup_test_tenant(self):
        """Create or get test tenant with domain"""
        try:
            from django.core.management import call_command

            with schema_context("public"):
                # Delete existing test tenant if it exists
                School.objects.filter(schema_name="test").delete()
                Domain.objects.filter(domain="testserver").delete()

                # Create new test tenant
                test_tenant = School.objects.create(
                    name="Test School",
                    schema_name="test",
                    subdomain="test",
                    address="Test Address",
                    contact_email="test@school.com",
                    contact_phone="1234567890",
                    board_affiliation="CBSE",
                    student_strength=0,
                    staff_count=0,
                    principal_name="Test Principal",
                    principal_email="principal@test.com",
                    principal_phone="0987654321",
                    is_approved=True,
                    academic_year_start=4,
                    academic_year_end=3,
                )

                # Create domain for test tenant
                Domain.objects.create(
                    domain="testserver", tenant=test_tenant, is_primary=True
                )

                self.stdout.write(
                    self.style.SUCCESS("Test tenant created successfully")
                )

                # Switch to test schema and run migrations
                connection.set_schema("test")
                call_command("migrate")

                # Create academic year
                from apps.academic.models import AcademicYear
                from datetime import date

                current_year = date.today().year
                AcademicYear.objects.create(
                    year=current_year,
                    start_date=date(current_year, 4, 1),
                    end_date=date(current_year + 1, 3, 31),
                    is_active=True,
                )

                self.stdout.write(
                    self.style.SUCCESS("Academic year created successfully")
                )
                return test_tenant

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error creating test tenant: {str(e)}"))
            return None

    def get_token(self, user):
        """Get JWT token for user"""
        try:
            refresh = RefreshToken.for_user(user)
            token = str(refresh.access_token)
            self.stdout.write(self.style.SUCCESS(f"Token generated for {user.email}"))
            return token
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Error generating token for {user.email}: {str(e)}")
            )
            return None

    def test_endpoint(self, token, endpoint, method="GET", data=None):
        """Test API endpoint with authentication"""
        client = Client(HTTP_HOST="testserver")
        url = f"/api/v1{endpoint}"

        try:
            # Set up headers with proper authentication
            headers = {}
            if token:
                headers["HTTP_AUTHORIZATION"] = f"Bearer {token}"
            headers["HTTP_ACCEPT"] = "application/json"
            headers["HTTP_X_REQUESTED_WITH"] = "XMLHttpRequest"

            # Make the request
            if method == "GET":
                response = client.get(url, **headers)
            elif method == "POST":
                response = client.post(
                    url,
                    data=json.dumps(data) if data else None,
                    content_type="application/json",
                    **headers,
                )
            elif method == "PUT":
                response = client.put(
                    url,
                    data=json.dumps(data) if data else None,
                    content_type="application/json",
                    **headers,
                )
            elif method == "DELETE":
                response = client.delete(url, **headers)
            else:
                self.stdout.write(self.style.ERROR(f"Unsupported method: {method}"))
                return None

            # Log response details
            self.stdout.write(
                f"    {method}: {response.status_code} {'[✓]' if response.status_code < 400 else '[✗]'}"
            )
            if response.status_code >= 400:
                self.stdout.write(
                    self.style.ERROR(f"      Error: {response.content.decode()}")
                )
            elif response.content:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"      Success: {response.content.decode()[:200]}..."
                    )
                )

            return response
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Request failed for {method} {url}: {str(e)}")
            )
            return None

    def handle(self, *args, **options):
        User = get_user_model()

        # Set up test tenant and switch to its schema
        test_tenant = self.setup_test_tenant()

        # Create test users in test tenant schema
        with schema_context("test"):
            try:
                # Clean up existing test data
                User.objects.filter(email__endswith="@test.com").delete()
                TeacherProfile.objects.all().delete()
                StudentProfile.objects.all().delete()

                # Create super admin
                super_admin = User.objects.create(
                    username="superadmin_test",
                    email="superadmin@test.com",
                    password="Test@123",
                    role="SUPER_ADMIN",
                    is_active=True,
                    is_staff=True,
                    is_superuser=True,
                )
                super_admin.set_password("Test@123")
                super_admin.save()

                # Create school admin
                school_admin = User.objects.create(
                    username="schooladmin_test",
                    email="schooladmin@test.com",
                    password="Test@123",
                    role="SCHOOL_ADMIN",
                    is_active=True,
                    is_staff=True,
                )
                school_admin.set_password("Test@123")
                school_admin.save()

                # Create teacher
                teacher = User.objects.create(
                    username="teacher_test",
                    email="teacher@test.com",
                    password="Test@123",
                    role="TEACHER",
                    is_active=True,
                )
                teacher.set_password("Test@123")
                teacher.save()

                TeacherProfile.objects.create(
                    user=teacher,
                    employee_id="EMP001",
                    date_of_birth="1990-01-01",
                    qualification="B.Ed",
                    experience_years=5,
                    subjects=["Mathematics", "Science"],
                )

                # Create student
                student = User.objects.create(
                    username="student_test",
                    email="student@test.com",
                    password="Test@123",
                    role="STUDENT",
                    is_active=True,
                )
                student.set_password("Test@123")
                student.save()

                StudentProfile.objects.create(
                    user=student,
                    admission_number="TEST001",
                    date_of_birth="2000-01-01",
                    gender="M",
                    blood_group="A+",
                    parent_name="Test Parent",
                    parent_phone="1234567890",
                    parent_email="parent@test.com",
                )

                self.stdout.write(self.style.SUCCESS("Test users created successfully"))

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"Error creating test users: {str(e)}")
                )

        # Switch to test schema for testing
        connection.set_schema("test")

        # Test endpoints for each role
        endpoints = {
            "students": {
                "path": "/academic/students/",
                "allowed_roles": ["super_admin", "school_admin", "teacher"],
                "methods": ["GET", "POST"],
            },
            "teachers": {
                "path": "/academic/teachers/",
                "allowed_roles": ["super_admin", "school_admin"],
                "methods": ["GET", "POST"],
            },
            "sections": {
                "path": "/academic/sections/",
                "allowed_roles": ["super_admin", "school_admin", "teacher"],
                "methods": ["GET"],
            },
            "classes": {
                "path": "/academic/classes/",
                "allowed_roles": ["super_admin", "school_admin", "teacher"],
                "methods": ["GET"],
            },
            "subjects": {
                "path": "/academic/subjects/",
                "allowed_roles": ["super_admin", "school_admin", "teacher"],
                "methods": ["GET"],
            },
            "library_books": {
                "path": "/library/books/",
                "allowed_roles": ["super_admin", "school_admin", "teacher", "student"],
                "methods": ["GET"],
            },
            "fees": {
                "path": "/finance/fees/",
                "allowed_roles": ["super_admin", "school_admin"],
                "methods": ["GET", "POST"],
            },
        }

        # Test each role's access
        roles = {
            "super_admin": User.objects.filter(
                username__startswith="superadmin_"
            ).first(),
            "school_admin": User.objects.filter(
                username__startswith="schooladmin_"
            ).first(),
            "teacher": User.objects.filter(username__startswith="teacher_").first(),
            "student": User.objects.filter(username__startswith="student_").first(),
        }

        self.stdout.write("\nTesting role-based access control...")
        for role_name, user in roles.items():
            if not user:
                self.stdout.write(f"Warning: {role_name} user not found")
                continue

            token = self.get_token(user)
            self.stdout.write(f"\nTesting {role_name.upper()} access:")

            for endpoint_name, endpoint_config in endpoints.items():
                self.stdout.write(f"\n  Testing {endpoint_name}:")
                for method in endpoint_config["methods"]:
                    response = self.test_endpoint(
                        token, endpoint_config["path"], method
                    )
                    if response:
                        status = response.status_code
                        expected_status = (
                            200
                            if role_name in endpoint_config["allowed_roles"]
                            else 403
                        )

                        result = "✓" if status == expected_status else "✗"
                        color = (
                            self.style.SUCCESS if result == "✓" else self.style.ERROR
                        )

                        self.stdout.write(
                            color(
                                f"    {method}: {status} [{result}] "
                                f"{'(Access Denied)' if status == 403 else ''}"
                            )
                        )

        # Test free tier limits
        self.stdout.write("\nTesting free tier limits...")
        admin_token = self.get_token(roles["school_admin"])

        # Test student limit (500)
        self.stdout.write("\nTesting student limit (500):")
        for i in range(500):
            student_data = {
                "email": f"student{i+1}@test.com",
                "password": "Test@123",
                "role": "STUDENT",
                "admission_number": f"TEST{i+1:03d}",
                "date_of_birth": "2000-01-01",
                "gender": "M",
                "blood_group": "A+",
                "parent_name": "Test Parent",
                "parent_phone": "1234567890",
                "parent_email": f"parent{i+1}@test.com",
            }
            response = self.test_endpoint(
                admin_token, "/academic/students/", "POST", student_data
            )
            if i % 100 == 0:
                self.stdout.write(f"  Created {i} students...")

        # Try creating 501st student
        self.stdout.write("\nAttempting to create 501st student:")
        student_data = {
            "email": "student501@test.com",
            "password": "Test@123",
            "role": "STUDENT",
            "admission_number": "TEST501",
            "date_of_birth": "2000-01-01",
            "gender": "M",
            "blood_group": "A+",
            "parent_name": "Test Parent",
            "parent_phone": "1234567890",
            "parent_email": "parent501@test.com",
        }
        response = self.test_endpoint(
            admin_token, "/academic/students/", "POST", student_data
        )
        if response and response.status_code == 403:
            self.stdout.write(
                self.style.SUCCESS("  Free tier student limit enforced successfully")
            )
        else:
            self.stdout.write(
                self.style.ERROR("  Free tier student limit not enforced")
            )

        # Test staff limit (50)
        self.stdout.write("\nTesting staff limit (50):")
        for i in range(50):
            teacher_data = {
                "email": f"teacher{i+1}@test.com",
                "password": "Test@123",
                "role": "TEACHER",
                "employee_id": f"EMP{i+1:03d}",
                "date_of_birth": "1990-01-01",
                "qualification": "B.Ed",
                "experience_years": 5,
                "subjects": ["Mathematics", "Science"],
            }
            response = self.test_endpoint(
                admin_token, "/academic/teachers/", "POST", teacher_data
            )
            if i % 10 == 0:
                self.stdout.write(f"  Created {i} teachers...")

        # Try creating 51st teacher
        self.stdout.write("\nAttempting to create 51st teacher:")
        teacher_data = {
            "email": "teacher51@test.com",
            "password": "Test@123",
            "role": "TEACHER",
            "employee_id": "EMP051",
            "date_of_birth": "1990-01-01",
            "qualification": "B.Ed",
            "experience_years": 5,
            "subjects": ["Mathematics", "Science"],
        }
        response = self.test_endpoint(
            admin_token, "/academic/teachers/", "POST", teacher_data
        )
        if response and response.status_code == 403:
            self.stdout.write(
                self.style.SUCCESS("  Free tier staff limit enforced successfully")
            )
        else:
            self.stdout.write(self.style.ERROR("  Free tier staff limit not enforced"))

        # Test endpoint responses
        try:
            response_data = response.json()
            if isinstance(response_data, dict):
                count = response_data.get("count", 0)
                self.stdout.write(f"      Items: {count}")

                # Check free tier limits in GET responses
                if endpoint_name == "students":
                    if role_name == "teacher":
                        self.stdout.write(f"      Teacher can see {count} students")
                    elif count > 500:
                        self.stdout.write(
                            self.style.WARNING(
                                f"      Warning: Student count ({count}) exceeds free tier limit (500)"
                            )
                        )
                elif endpoint_name == "teachers" and count > 50:
                    self.stdout.write(
                        self.style.WARNING(
                            f"      Warning: Staff count ({count}) exceeds free tier limit (50)"
                        )
                    )
        except Exception as e:
            self.stdout.write(
                self.style.WARNING(f"      Could not parse response: {str(e)}")
            )

        if response and response.status_code not in [200, 403]:
            self.stdout.write(
                self.style.ERROR(f"      Error: {response.content.decode()}")
            )

        # Reset connection schema
        connection.set_schema_to_public()
