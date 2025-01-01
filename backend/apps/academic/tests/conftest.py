import pytest
from django.contrib.auth import get_user_model
from apps.core.models import School
from apps.academic.models import AcademicYear
from django_tenants.test.client import TenantClient
from django_tenants.utils import schema_context

User = get_user_model()

@pytest.fixture
def academic_year(test_school):
    """Create a test academic year."""
    with schema_context(test_school.schema_name):
        academic_year = AcademicYear.objects.create(
            name='2024-2025',
            start_date='2024-04-01',
            end_date='2025-03-31',
            start_month=4,
            end_month=3,
            school=test_school
        )
        return academic_year

@pytest.fixture
def authenticated_academic_client(test_school, test_user):
    """Create an authenticated client for academic tests."""
    client = TenantClient(test_school)
    client.force_login(test_user)
    client._credentials['HTTP_X_TENANT_ID'] = test_school.schema_name
    return client
