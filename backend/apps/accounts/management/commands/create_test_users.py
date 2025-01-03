from django.core.management.base import BaseCommand
from django.db import transaction
from apps.accounts.models import User, StudentProfile, TeacherProfile
from apps.core.models import School
from django.utils import timezone


class Command(BaseCommand):
    help = "Creates test users with different roles for development"

    def handle(self, *args, **kwargs):
        try:
            with transaction.atomic():
                # Get the default school
                school = School.objects.get(schema_name="public")

                # Create a super admin with timestamp
                timestamp = timezone.now().strftime("%Y%m%d%H%M%S")
                super_admin = User.objects.create_superuser(
                    username=f"superadmin_{timestamp}",
                    email=f"superadmin_{timestamp}@test.com",
                    password="Test@123",
                    first_name="Super",
                    last_name="Admin",
                    role="super_admin",
                    school=school,
                )
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Created super admin user: {super_admin.username}"
                    )
                )

                # Create a school admin with timestamp
                school_admin = User.objects.create_user(
                    username=f"schooladmin_{timestamp}",
                    email=f"schooladmin_{timestamp}@test.com",
                    password="Test@123",
                    first_name="School",
                    last_name="Admin",
                    role="school_admin",
                    school=school,
                )
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Created school admin user: {school_admin.username}"
                    )
                )

                # Create a teacher with timestamp
                teacher = User.objects.create_user(
                    username=f"teacher_{timestamp}",
                    email=f"teacher_{timestamp}@test.com",
                    password="Test@123",
                    first_name="Test",
                    last_name="Teacher",
                    role="teacher",
                    school=school,
                )
                TeacherProfile.objects.create(
                    user=teacher,
                    employee_id=f"EMP{timestamp}",
                    date_of_birth=timezone.now().date(),
                    qualification="B.Ed",
                    experience_years=5,
                    subjects=["Mathematics", "Science"],
                )
                self.stdout.write(
                    self.style.SUCCESS(f"Created teacher user: {teacher.username}")
                )

                # Create a student with timestamp
                student = User.objects.create_user(
                    username=f"student_{timestamp}",
                    email=f"student_{timestamp}@test.com",
                    password="Test@123",
                    first_name="Test",
                    last_name="Student",
                    role="student",
                    school=school,
                )
                StudentProfile.objects.create(
                    user=student,
                    admission_number=f"ADM{timestamp}",
                    date_of_birth=timezone.now().date(),
                    gender="M",
                    blood_group="A+",
                    parent_name="Parent Name",
                    parent_phone="1234567890",
                    parent_email=f"parent_{timestamp}@test.com",
                )
                self.stdout.write(
                    self.style.SUCCESS(f"Created student user: {student.username}")
                )

                # Create a parent with timestamp
                parent = User.objects.create_user(
                    username=f"parent_{timestamp}",
                    email=f"parent_{timestamp}@test.com",
                    password="Test@123",
                    first_name="Test",
                    last_name="Parent",
                    role="parent",
                    school=school,
                )
                self.stdout.write(
                    self.style.SUCCESS(f"Created parent user: {parent.username}")
                )

                self.stdout.write(
                    self.style.SUCCESS(
                        "\nAll test users created successfully!\n"
                        "Credentials for all users:\n"
                        "Username: [superadmin, schooladmin, teacher, student, parent]\n"
                        "Password: Test@123"
                    )
                )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Failed to create test users: {str(e)}")
            )
            raise
