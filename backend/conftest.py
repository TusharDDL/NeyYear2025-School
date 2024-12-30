import pytest
from django.core.management import call_command
from django_tenants.utils import schema_context, tenant_context
from django_tenants.middleware import TenantMiddleware
from django_tenants.test.client import TenantClient
from django.test.client import RequestFactory
from django.conf import settings
from django.db import connection
from apps.core.models import School, Domain
from django.utils import timezone

@pytest.fixture(scope='session')
def django_db_setup(django_db_blocker):
    """Set up the test database for multi-tenant testing."""
    settings.DATABASES['default']['NAME'] = 'test_' + settings.DATABASES['default']['NAME']
    
    with django_db_blocker.unblock():
        # Drop and recreate schemas
        with connection.cursor() as cursor:
            cursor.execute("DROP SCHEMA IF EXISTS public CASCADE")
            cursor.execute("CREATE SCHEMA public")
            cursor.execute("GRANT ALL ON SCHEMA public TO PUBLIC")
        
        # Run migrations for public schema first
        with schema_context('public'):
            # Temporarily disable django-tenants middleware
            original_middleware = settings.MIDDLEWARE
            original_routers = settings.DATABASE_ROUTERS
            settings.MIDDLEWARE = [m for m in settings.MIDDLEWARE if not m.startswith('django_tenants')]
            settings.DATABASE_ROUTERS = []
            
            try:
                # Run all migrations in public schema
                call_command('migrate', verbosity=0, interactive=False)
            finally:
                # Restore original settings
                settings.MIDDLEWARE = original_middleware
                settings.DATABASE_ROUTERS = original_routers

@pytest.fixture(scope='function')
def tenant(django_db_setup, django_db_blocker):
    """Create a test tenant with proper cleanup."""
    from django.contrib.auth import get_user_model
    from django.db import connection, connections
    from django.db import transaction
    
    User = get_user_model()
    
    def _create_tenant():
        """Create a test school tenant with consistent ID."""
        # Close all existing connections
        for conn in connections.all():
            conn.close()
        
        # Ensure we're in public schema with a fresh connection
        connection.set_schema_to_public()
        connection.close()
        connection.connect()
        
        with transaction.atomic():
            with schema_context('public'):
                # Clean up any existing test data
                School.objects.filter(schema_name__startswith='test_').delete()
                Domain.objects.filter(domain__startswith='test_').delete()
                
                # Reset sequences to ensure consistent IDs
                with connection.cursor() as cursor:
                    cursor.execute("SELECT pg_catalog.setval(pg_get_serial_sequence('core_school', 'id'), 1, false);")
                    cursor.execute("SELECT pg_catalog.setval(pg_get_serial_sequence('core_domain', 'id'), 1, false);")
                    cursor.execute("SELECT pg_catalog.setval(pg_get_serial_sequence('accounts_user', 'id'), 1, false);")
                
                import time
                timestamp = str(int(time.time()))
                schema_name = f'test_school_{timestamp}'
                
                # Create school in public schema
                school = School.objects.create(
                    schema_name=schema_name,
                    name=f'Test School {timestamp}',
                    address='Test Address',
                    contact_email=f'test_{timestamp}@school.com',
                    contact_phone='1234567890',
                    board_affiliation='CBSE',
                    student_strength=100,
                    staff_count=10,
                    principal_name=f'Test Principal {timestamp}',
                    principal_email=f'principal_{timestamp}@test.com',
                    principal_phone='0987654321',
                    is_approved=True,
                    approval_date=timezone.now(),
                    academic_year_start=4,
                    academic_year_end=3
                )
            
            # Create domain for the school
            Domain.objects.create(
                domain=f'test.{schema_name}.localhost',
                tenant=school,
                is_primary=True
            )
            
            return school
    
    def _setup_tenant_schema(school):
        with schema_context(school.schema_name):
            # Run migrations
            call_command('migrate', verbosity=0, interactive=False)
            
            # Create groups
            from django.contrib.auth.models import Group, Permission
            groups = ['ADMIN', 'TEACHER', 'STUDENT', 'PARENT', 'LIBRARIAN', 'ACCOUNTANT']
            created_groups = {}
            for group_name in groups:
                group, _ = Group.objects.get_or_create(name=group_name)
                created_groups[group_name] = group
            
            # Create test admin user with unique username
            import time
            timestamp = str(int(time.time()))
            admin_user = User.objects.create_user(
                username=f'admin_{school.schema_name}_{timestamp}',
                email=f'test_admin_{timestamp}@test.com',
                password='testpass123',
                is_staff=True,
                is_superuser=True,
                role='school_admin',
                school=school
            )
            admin_user.groups.add(created_groups['ADMIN'])
            
            # Assign all permissions to admin group
            created_groups['ADMIN'].permissions.add(*Permission.objects.all())
    
    with django_db_blocker.unblock():
        try:
            school = _create_tenant()
            _setup_tenant_schema(school)
            
            # Ensure we're in the correct schema before yielding
            connection.set_schema_to_public()
            connection.close()
            connection.connect()
            
            with schema_context(school.schema_name):
                yield school
        finally:
            # Cleanup after test
            for conn in connections.all():
                conn.close()
            
            connection.connect()
            with transaction.atomic():
                with schema_context('public'):
                    School.objects.filter(schema_name__startswith='test_').delete()
                    with connection.cursor() as cursor:
                        cursor.execute(f"DROP SCHEMA IF EXISTS {school.schema_name} CASCADE")
            
            connection.close()
            connection.set_schema_to_public()
            connection.connect()


@pytest.fixture
def api_client(tenant):
    """Create a tenant-aware test client."""
    from rest_framework.test import APIClient
    from django_tenants.test.client import TenantRequestFactory
    
    class TenantAwareAPIClient(APIClient):
        def __init__(self, tenant, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.tenant = tenant
            self.factory = TenantRequestFactory(tenant)
            self._force_user = None
            self._force_token = None
        
        def force_authenticate(self, user=None, token=None):
            """Override force_authenticate to properly set user and token."""
            if not hasattr(self, '_force_authenticate_called'):
                self._force_authenticate_called = True
                try:
                    super().force_authenticate(user=user, token=token)
                    self._force_user = user
                    self._force_token = token
                finally:
                    delattr(self, '_force_authenticate_called')
    
    client = TenantAwareAPIClient(tenant)
    return client

@pytest.fixture(autouse=True)
def use_tenant_context(tenant):
    """Automatically use tenant context for all tests."""
    from django_tenants.utils import schema_context
    from django.db import connection, connections
    
    # Close all existing connections
    for conn in connections.all():
        conn.close()
    
    # Set up new connection in tenant context
    with schema_context(tenant.schema_name):
        connection.set_tenant(tenant)
        connection.ensure_connection()  # Ensure we have a fresh connection
        try:
            yield
        finally:
            # Clean up connections
            for conn in connections.all():
                conn.close()
            connection.set_schema_to_public()
            connection.ensure_connection()  # Ensure we have a fresh public connection

@pytest.fixture(autouse=True)
def cleanup_test_schemas(request, django_db_blocker):
    """Clean up test schemas after tests."""
    def cleanup():
        from django.db import connection, connections, transaction
        from django_tenants.utils import schema_context
        
        with django_db_blocker.unblock():
            # Close all existing connections
            for conn in connections.all():
                conn.close()
            
            # Ensure we're in public schema with a fresh connection
            connection.set_schema_to_public()
            connection.close()
            connection.connect()
            
            try:
                with transaction.atomic():
                    with schema_context('public'):
                        # Clean up test schools and their schemas
                        schools = School.objects.filter(schema_name__startswith='test_')
                        for school in schools:
                            with connection.cursor() as cursor:
                                cursor.execute(f"DROP SCHEMA IF EXISTS {school.schema_name} CASCADE")
                        schools.delete()
                        Domain.objects.filter(domain__startswith='test.').delete()
            except Exception as e:
                print(f"Error during cleanup: {e}")
            finally:
                # Ensure we're back in public schema with a fresh connection
                connection.close()
                connection.set_schema_to_public()
                connection.connect()
    
    request.addfinalizer(cleanup)
