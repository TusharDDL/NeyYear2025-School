import pytest
from django.contrib.auth import get_user_model
from apps.core.models import School
from apps.library.models import Book
from django_tenants.test.client import TenantClient
from django_tenants.utils import schema_context

User = get_user_model()

@pytest.fixture
def test_librarian(tenant):
    """Create a test librarian user."""
    with schema_context(tenant.schema_name):
        librarian = User.objects.create_user(
            username=f'test_librarian_{tenant.schema_name}',
            email=f'librarian@{tenant.schema_name}',
            password='testpass123',
            role='librarian',
            school=tenant
        )
        return librarian

@pytest.fixture
def test_book(tenant):
    """Create a test book."""
    with schema_context(tenant.schema_name):
        book = Book.objects.create(
            title='Test Book',
            author='Test Author',
            isbn='1234567890123',
            publisher='Test Publisher',
            publication_year=2024,
            copies=1,
            available_copies=1,
            school=tenant
        )
        return book

@pytest.fixture
def library_client(tenant, test_librarian):
    """Create an authenticated client for library tests."""
    client = TenantClient(tenant)
    client.force_login(test_librarian)
    return client
