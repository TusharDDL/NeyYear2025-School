import pytest
from django.urls import reverse
from rest_framework import status
from django_tenants.test.client import TenantClient
from django.db import transaction
from apps.academic.models import AcademicYear
from apps.core.models import School, Domain
from apps.accounts.models import User
from django_tenants.utils import schema_context
from datetime import date

# Using fixtures from root conftest.py


@pytest.mark.django_db(transaction=True)
@pytest.mark.tenant
class TestAcademicYear:
    @pytest.mark.django_db(transaction=True)
    def test_create_academic_year(self, api_client, tenant, admin_user):
        """Test creating an academic year."""
        from django_tenants.utils import schema_context
        from django.db import connection
        import logging

        logger = logging.getLogger("apps.academic.tests")
        logger.info(
            f"Starting test_create_academic_year for tenant: {tenant.schema_name}"
        )

        # Set up tenant context for the entire test
        with schema_context(tenant.schema_name):
            connection.set_tenant(tenant)

            api_client.force_authenticate(user=admin_user)
            url = "/api/v1/academic/academic-years/"
            data = {
                "name": "2024-2025",
                "start_date": "2024-04-01",
                "end_date": "2025-03-31",
                "start_month": 4,  # April
                "end_month": 3,  # March
            }

            # Verify schema before request
            current_schema = connection.schema_name
            logger.info(f"Current schema before request: {current_schema}")
            assert (
                current_schema == tenant.schema_name
            ), f"Wrong schema before request: {current_schema} != {tenant.schema_name}"

            # Make request
            response = api_client.post(url, data)
            logger.info(
                f"Response status: {response.status_code}, content: {response.content}"
            )
            assert (
                response.status_code == status.HTTP_201_CREATED
            ), f"Response content: {response.content}"

            # Re-establish connection and verify schema
            connection.close()
            connection.connect()
            connection.set_tenant(tenant)

            # Verify schema after request
            current_schema = connection.schema_name
            logger.info(f"Current schema after request: {current_schema}")
            assert (
                current_schema == tenant.schema_name
            ), f"Wrong schema after request: {current_schema} != {tenant.schema_name}"

            # Query within explicit schema context to verify data
            with schema_context(tenant.schema_name):
                count = AcademicYear.objects.count()
                logger.info(f"Found {count} academic years in schema {current_schema}")
                assert count == 1, "No academic year was created"

            academic_year = AcademicYear.objects.first()
            assert academic_year is not None, "Academic year object is None"
            assert academic_year.name == "2024-2025"
            assert academic_year.school == tenant
            assert academic_year.start_month == 4
            assert academic_year.end_month == 3

    @pytest.mark.django_db(transaction=True)
    def test_create_overlapping_academic_year(self, api_client, tenant, admin_user):
        """Test that creating overlapping academic years fails."""
        from django_tenants.utils import schema_context

        api_client.force_authenticate(user=admin_user)

        with schema_context(tenant.schema_name):
            # Create first academic year
            AcademicYear.objects.create(
                name="2024-2025",
                start_date=date(2024, 4, 1),
                end_date=date(2025, 3, 31),
                start_month=4,  # April
                end_month=3,  # March
                school=tenant,
            )

            url = "/api/v1/academic/academic-years/"
            data = {
                "name": "2024-2025 Overlap",
                "start_date": "2024-06-01",
                "end_date": "2025-05-31",
                "start_month": 6,  # June
                "end_month": 5,  # May
            }
            response = api_client.post(url, data)
            assert (
                response.status_code == status.HTTP_400_BAD_REQUEST
            ), f"Response content: {response.content}"
            assert "Academic year dates overlap" in str(response.content)

    @pytest.mark.django_db(transaction=True)
    def test_list_academic_years(self, api_client, tenant, admin_user):
        """Test listing academic years."""
        from django_tenants.utils import schema_context
        from django.db import transaction, connection
        import logging

        logger = logging.getLogger("apps.academic.tests")
        logger.info(
            f"Starting test_list_academic_years for tenant: {tenant.schema_name}"
        )

        api_client.force_authenticate(user=admin_user)

        # Create academic years in tenant schema
        with schema_context(tenant.schema_name):
            connection.set_tenant(tenant)
            with transaction.atomic():
                logger.info("Creating test academic years")
                # Create test academic years
                AcademicYear.objects.create(
                    name="2024-2025",
                    start_date=date(2024, 4, 1),
                    end_date=date(2025, 3, 31),
                    start_month=4,  # April
                    end_month=3,  # March
                    school=tenant,
                )
                AcademicYear.objects.create(
                    name="2025-2026",
                    start_date=date(2025, 4, 1),
                    end_date=date(2026, 3, 31),
                    start_month=4,  # April
                    end_month=3,  # March
                    school=tenant,
                )

            # Verify academic years were created
            count = AcademicYear.objects.count()
            logger.info(f"Created {count} academic years")
            assert count == 2, f"Expected 2 academic years, found {count}"

            # Make API request in tenant context
            url = "/api/v1/academic/academic-years/"
            logger.info(f"Making GET request to {url}")
            response = api_client.get(url)
            logger.info(
                f"Response status: {response.status_code}, content: {response.content}"
            )

            # Verify response
            assert (
                response.status_code == status.HTTP_200_OK
            ), f"Response content: {response.content}"
            assert "count" in response.data, "Response missing count field"
            assert (
                response.data["count"] == 2
            ), f"Expected 2 academic years, got {response.data['count']}"
            assert (
                len(response.data["results"]) == 2
            ), f"Expected 2 results, got {len(response.data['results'])}"

            # Verify academic years still exist after request
            final_count = AcademicYear.objects.count()
            logger.info(f"Final academic year count: {final_count}")
            assert (
                final_count == 2
            ), f"Expected 2 academic years after request, found {final_count}"

    @pytest.mark.django_db(transaction=True)
    def test_update_academic_year(self, api_client, tenant, admin_user):
        """Test updating an academic year."""
        from django_tenants.utils import schema_context
        from django.db import connection, transaction
        import logging

        logger = logging.getLogger("apps.academic.tests")
        logger.info(
            f"Starting test_update_academic_year for tenant: {tenant.schema_name}"
        )

        api_client.force_authenticate(user=admin_user)

        # Set up tenant context for the entire test
        with schema_context(tenant.schema_name):
            connection.set_tenant(tenant)
            with transaction.atomic():
                # Create initial academic year
                logger.info("Creating initial academic year")
                academic_year = AcademicYear.objects.create(
                    name="2024-2025",
                    start_date=date(2024, 4, 1),
                    end_date=date(2025, 3, 31),
                    start_month=4,  # April
                    end_month=3,  # March
                    school=tenant,
                )
                logger.info(f"Created academic year with ID: {academic_year.pk}")

                # Verify academic year was created
                assert AcademicYear.objects.filter(
                    pk=academic_year.pk
                ).exists(), "Academic year was not created"

                # Update academic year
                url = f"/api/v1/academic/academic-years/{academic_year.pk}/"
                data = {
                    "name": "2024-2025 Updated",
                    "start_date": "2024-04-01",
                    "end_date": "2025-03-31",
                    "start_month": 4,  # April
                    "end_month": 3,  # March
                }

                logger.info(f"Making PUT request to {url} with data: {data}")
                response = api_client.put(url, data)
                logger.info(
                    f"Response status: {response.status_code}, content: {response.content}"
                )
                assert (
                    response.status_code == status.HTTP_200_OK
                ), f"Response content: {response.content}"

                # Verify update in the same schema context
                updated = AcademicYear.objects.get(pk=academic_year.pk)
                assert updated.name == "2024-2025 Updated", "Name was not updated"
                assert (
                    updated.start_date.strftime("%Y-%m-%d") == "2024-04-01"
                ), "Start date was not updated"
                assert (
                    updated.end_date.strftime("%Y-%m-%d") == "2025-03-31"
                ), "End date was not updated"

    @pytest.mark.django_db(transaction=True)
    def test_delete_academic_year(self, api_client, tenant, admin_user):
        """Test deleting an academic year."""
        from django_tenants.utils import schema_context
        from django.db import transaction, connection
        import logging

        logger = logging.getLogger("apps.academic.tests")
        logger.info(
            f"Starting test_delete_academic_year for tenant: {tenant.schema_name}"
        )

        api_client.force_authenticate(user=admin_user)

        with schema_context(tenant.schema_name):
            connection.set_tenant(tenant)
            with transaction.atomic():
                logger.info("Creating academic year for deletion test")
                academic_year = AcademicYear.objects.create(
                    name="2024-2025",
                    start_date=date(2024, 4, 1),
                    end_date=date(2025, 3, 31),
                    start_month=4,  # April
                    end_month=3,  # March
                    school=tenant,
                )
                logger.info(f"Created academic year with ID: {academic_year.pk}")

                url = f"/api/v1/academic/academic-years/{academic_year.pk}/"
                logger.info(f"Making DELETE request to {url}")
                response = api_client.delete(url)
                logger.info(f"Response status: {response.status_code}")
                assert (
                    response.status_code == status.HTTP_204_NO_CONTENT
                ), f"Response content: {response.content}"

                count = AcademicYear.objects.count()
                logger.info(f"Academic year count after deletion: {count}")
                assert count == 0, "Academic year was not deleted"
