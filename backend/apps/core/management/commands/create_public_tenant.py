from django.core.management.base import BaseCommand
from apps.core.models import School, Domain
from django.db import connection


class Command(BaseCommand):
    help = "Creates the public tenant for multi-tenant setup"

    def handle(self, *args, **options):
        try:
            # Create public tenant
            public_tenant = School.objects.create(
                schema_name="public",
                name="Public School",
                address="123 Public School Road, City",
                contact_email="admin@publicschool.com",
                contact_phone="1234567890",
                board_affiliation="CBSE",
                student_strength=100,
                staff_count=20,
                principal_name="John Doe",
                principal_email="principal@publicschool.com",
                principal_phone="9876543210",
                academic_year_start=4,
                academic_year_end=3,
                is_approved=True,
            )

            # Create domain for the tenant
            Domain.objects.create(
                domain="localhost", tenant=public_tenant, is_primary=True
            )

            self.stdout.write(self.style.SUCCESS("Successfully created public tenant"))

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Failed to create public tenant: {str(e)}")
            )
