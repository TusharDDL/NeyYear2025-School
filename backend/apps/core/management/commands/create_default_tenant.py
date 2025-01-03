# apps/core/management/commands/create_default_tenant.py

from django.core.management.base import BaseCommand
from django.db import transaction
from apps.core.models import School, Domain
from django.utils import timezone


class Command(BaseCommand):
    help = "Creates a default tenant for development"

    def handle(self, *args, **kwargs):
        try:
            with transaction.atomic():
                # Create the default school/tenant
                school = School.objects.create(
                    schema_name="public",
                    name="Default School",
                    address="123 Default Street",
                    contact_email="admin@defaultschool.com",
                    contact_phone="1234567890",
                    board_affiliation="CBSE",
                    student_strength=100,  # Within free tier limit of 500
                    staff_count=10,  # Within free tier limit of 50
                    principal_name="Default Principal",
                    principal_email="principal@defaultschool.com",
                    principal_phone="1234567890",
                    is_active=True,
                    is_approved=True,
                    approval_date=timezone.now(),
                    academic_year_start=4,  # April
                    academic_year_end=3,  # March
                    auto_create_schema=True,
                )

                # Create the domain for the school
                Domain.objects.create(
                    domain="localhost", tenant=school, is_primary=True
                )

                self.stdout.write(
                    self.style.SUCCESS(
                        f"Successfully created default tenant: {school.name} with domain: localhost"
                    )
                )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Failed to create default tenant: {str(e)}")
            )
            raise
