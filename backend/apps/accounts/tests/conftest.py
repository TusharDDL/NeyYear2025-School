import pytest
from django.contrib.auth import get_user_model
from apps.core.models import School
from django_tenants.test.client import TenantClient
from django_tenants.utils import schema_context
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()

@pytest.fixture
def auth_client(tenant, test_user):
    """Create an authenticated client."""
    client = TenantClient(tenant)
    client.force_login(test_user)
    return client

@pytest.fixture
def test_tokens(test_user):
    """Generate JWT tokens for test user."""
    refresh = RefreshToken.for_user(test_user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }

@pytest.fixture
def student_user(tenant):
    """Create a test student user."""
    with schema_context(tenant.schema_name):
        user = User.objects.create_user(
            username=f'test_student_{tenant.schema_name}',
            email=f'student@{tenant.schema_name}',
            password='testpass123',
            role='student',
            school=tenant
        )
        return user
