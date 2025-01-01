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
        from django_tenants.utils import tenant_context, schema_context, get_public_schema_name
        from django.db import transaction
        import time
        
        # Close all existing connections and ensure we're in public schema
        for conn in connections.all():
            conn.close()
        connection.set_schema_to_public()
        connection.ensure_connection()
        
        timestamp = str(int(time.time()))
        schema_name = f'test_school_{timestamp}'
        school = None
        
        try:
            # Clean up any existing test data in public schema
            School.objects.filter(schema_name__startswith='test_').delete()
            Domain.objects.filter(domain__startswith='test_').delete()
            
            # Reset sequences for consistent IDs
            with connection.cursor() as cursor:
                cursor.execute("SELECT pg_catalog.setval(pg_get_serial_sequence('core_school', 'id'), 1, false);")
                cursor.execute("SELECT pg_catalog.setval(pg_get_serial_sequence('core_domain', 'id'), 1, false);")
                cursor.execute("SELECT pg_catalog.setval(pg_get_serial_sequence('accounts_user', 'id'), 1, false);")
                
                # Create schema if it doesn't exist
                cursor.execute(f"DROP SCHEMA IF EXISTS {schema_name} CASCADE")
                cursor.execute(f"CREATE SCHEMA {schema_name}")
                cursor.execute(f"GRANT ALL ON SCHEMA {schema_name} TO PUBLIC")
            
            # Create school in public schema
            with schema_context(get_public_schema_name()):
                with transaction.atomic():
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
                        academic_year_end=3,
                        auto_create_schema=False  # Prevent automatic schema creation
                    )
                
                # Create domain for the school
                Domain.objects.create(
                    domain=f'{schema_name}.localhost',
                    tenant=school,
                    is_primary=True
                )
            
            # Run migrations in the new schema
            connection.set_schema(schema_name)
            call_command('migrate', verbosity=0, interactive=False)
            
            # Copy school data to tenant schema using raw SQL
            with connection.cursor() as cursor:
                cursor.execute(f"""
                    INSERT INTO {schema_name}.core_school 
                    SELECT * FROM public.core_school WHERE id = %s
                """, [school.id])
            
            connection.set_schema_to_public()
            return school
            
        except Exception as e:
            # Clean up on failure
            if schema_name:
                with connection.cursor() as cursor:
                    cursor.execute(f"DROP SCHEMA IF EXISTS {schema_name} CASCADE")
            connection.set_schema_to_public()
            raise
        except Exception as e:
            if school and school.schema_name:
                # Clean up on failure
                with connection.cursor() as cursor:
                    cursor.execute(f"DROP SCHEMA IF EXISTS {schema_name} CASCADE")
            raise
    
    def _setup_tenant_schema(school):
        """Set up the tenant schema with necessary initial data."""
        from django.contrib.auth.models import Group, Permission
        from django.contrib.contenttypes.models import ContentType
        from django.db import connection, transaction
        import time
        
        try:
            # Ensure we're in public schema first
            connection.set_schema_to_public()
            
            # Verify school exists in public schema
            public_school = School.objects.get(id=school.id)
            
            with schema_context(school.schema_name):
                # Copy school data to tenant schema if it doesn't exist
                try:
                    tenant_school = School.objects.get(id=school.id)
                except School.DoesNotExist:
                    # Copy school data using raw SQL to bypass model validation
                    with connection.cursor() as cursor:
                        cursor.execute(f"""
                            INSERT INTO {school.schema_name}.core_school 
                            SELECT * FROM public.core_school WHERE id = %s
                        """, [public_school.id])
                    tenant_school = School.objects.get(id=school.id)
                
                # Create groups
                groups = ['ADMIN', 'TEACHER', 'STUDENT', 'PARENT', 'LIBRARIAN', 'ACCOUNTANT']
                created_groups = {}
                for group_name in groups:
                    group, _ = Group.objects.get_or_create(name=group_name)
                    created_groups[group_name] = group
                
                # Create test admin user
                timestamp = str(int(time.time()))
                admin_user = User.objects.create_user(
                    username=f'admin_{school.schema_name}_{timestamp}',
                    email=f'test_admin_{timestamp}@test.com',
                    password='testpass123',
                    is_staff=True,
                    is_superuser=True,
                    role='school_admin',
                    school=tenant_school
                )
                admin_user.groups.add(created_groups['ADMIN'])
                
                # Assign all permissions to admin group
                content_types = ContentType.objects.all()
                permissions = Permission.objects.filter(content_type__in=content_types)
                created_groups['ADMIN'].permissions.add(*permissions)
                
                # Verify school is accessible
                School.objects.get(id=school.id)
        except Exception as e:
            print(f"Error in _setup_tenant_schema: {e}")
            connection.set_schema_to_public()
            raise
    
    with django_db_blocker.unblock():
        school = None
        try:
            # Ensure we start in public schema
            connection.set_schema_to_public()
            
            # Create tenant and set up schema
            school = _create_tenant()
            if school:
                _setup_tenant_schema(school)
                
                # Switch to tenant schema for test execution
                with schema_context(school.schema_name):
                    yield school
        finally:
            # Cleanup after test
            if school and hasattr(school, 'schema_name'):
                # Ensure we're in public schema for cleanup
                for conn in connections.all():
                    conn.close()
                connection.set_schema_to_public()
                connection.ensure_connection()
                
                # Clean up test data and schema
                with transaction.atomic():
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
            # Set up logging
            import logging
            self.logger = logging.getLogger('apps.core.tests')
            # Set default headers with properly formatted domain
            # Convert schema name to valid domain format (lowercase alphanumeric only)
            import re
            domain = re.sub(r'[^a-z0-9]', '', tenant.schema_name.lower())
            domain = f"{domain}.localhost"
            
            self.defaults = {
                'HTTP_HOST': domain,
                'SERVER_NAME': 'localhost',
                'HTTP_X_TENANT_ID': str(tenant.id),
                'HTTP_X_TENANT_SCHEMA': tenant.schema_name,
                'wsgi.url_scheme': 'http',
                'HTTP_X_FORWARDED_PROTO': 'http'
            }
            
            # Ensure domain is in ALLOWED_HOSTS
            from django.conf import settings
            if domain not in settings.ALLOWED_HOSTS:
                settings.ALLOWED_HOSTS.append(domain)
                self.logger.debug(f"Added {domain} to ALLOWED_HOSTS")
        
        def generic(self, method, path, *args, **kwargs):
            """Ensure all API requests go through /api/v1/ prefix and maintain tenant context."""
            from django_tenants.utils import tenant_context, schema_context
            from django.conf import settings
            from django.db import transaction, connection, connections
            from django.db.utils import InterfaceError, OperationalError
            
            # Normalize path
            if not path.startswith('/'):
                path = '/' + path
            if not path.startswith('/api/v1/'):
                path = '/api/v1/' + path.lstrip('/')
            
            # Update kwargs with default headers
            for key, value in self.defaults.items():
                kwargs.setdefault(key, value)
            
            def ensure_connection():
                """Ensure database connection is alive and in correct schema."""
                try:
                    if connection.connection is None or connection.connection.closed:
                        connection.close()
                        connection.connect()
                    if connection.schema_name != self.tenant.schema_name:
                        connection.set_tenant(self.tenant)
                except (InterfaceError, OperationalError) as e:
                    self.logger.warning(f"Database connection error: {e}")
                    connection.close()
                    connection.connect()
                    connection.set_tenant(self.tenant)
            
            # Use tenant context for the request
            try:
                # Set up fresh connection in tenant schema and maintain context
                with schema_context(self.tenant.schema_name):
                    # Close and reconnect to ensure clean connection
                    connection.close()
                    connection.connect()
                    
                    # Set tenant and verify schema
                    connection.set_tenant(self.tenant)
                    current_schema = connection.schema_name
                    self.logger.debug(f"Current schema before request: {current_schema}")
                    assert current_schema == self.tenant.schema_name, \
                        f"Wrong schema before request: {current_schema} != {self.tenant.schema_name}"
                    
                    # Make the request within the tenant context
                    response = super().generic(method, path, *args, **kwargs)
                    self.logger.debug(f"Request to {path} completed with status {response.status_code}")
                    
                    # Re-establish connection and verify schema after request
                    connection.close()
                    connection.connect()
                    connection.set_tenant(self.tenant)
                    current_schema = connection.schema_name
                    self.logger.debug(f"Current schema after request: {current_schema}")
                    assert current_schema == self.tenant.schema_name, \
                        f"Wrong schema after request: {current_schema} != {self.tenant.schema_name}"
                    
                    return response
            except Exception as e:
                self.logger.error(f"Error during request: {e}", exc_info=True)
                raise
        
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

@pytest.fixture
def admin_user(tenant):
    """Create an admin user for testing."""
    from django.contrib.auth import get_user_model
    from django_tenants.utils import schema_context
    
    User = get_user_model()
    
    with schema_context(tenant.schema_name):
        admin = User.objects.create_user(
            username=f'admin_{tenant.schema_name}',
            email=f'admin_{tenant.schema_name}@test.com',
            password='testpass123',
            is_staff=True,
            is_superuser=True,
            role='school_admin',
            school=tenant
        )
        return admin

@pytest.fixture(autouse=True)
def use_tenant_context(tenant):
    """Automatically use tenant context for all tests."""
    from django_tenants.utils import schema_context, get_public_schema_name
    from django.db import connection, connections, transaction
    import logging
    
    logger = logging.getLogger('apps.core.tests')
    
    # Close all existing connections
    for conn in connections.all():
        if not conn.connection.closed:
            conn.close()
    
    # Start in public schema with fresh connection
    connection.close()
    connection.connect()
    connection.set_schema_to_public()
    
    try:
        # Set up tenant context
        with transaction.atomic():
            with schema_context(tenant.schema_name):
                connection.set_tenant(tenant)
                logger.debug(f"Set up tenant context for {tenant.schema_name}")
                yield
    except Exception as e:
        logger.error(f"Error in tenant context: {e}", exc_info=True)
        raise
    finally:
        try:
            # Clean up connections properly
            for conn in connections.all():
                if not conn.connection.closed:
                    conn.close()
            
            # Ensure we're back in public schema
            connection.close()
            connection.connect()
            connection.set_schema_to_public()
            logger.debug("Cleaned up tenant context")
        except Exception as e:
            logger.error(f"Error cleaning up tenant context: {e}", exc_info=True)

@pytest.fixture(autouse=True)
def cleanup_test_schemas(request, django_db_blocker):
    """Clean up test schemas after tests."""
    def cleanup():
        from django.db import connection, connections, transaction
        from django_tenants.utils import schema_context
        import logging
        
        logger = logging.getLogger('apps.core.tests')
        logger.info("Starting test schema cleanup")
        
        with django_db_blocker.unblock():
            # Ensure all connections are closed
            for conn in connections.all():
                if not conn.connection.closed:
                    conn.close()
            
            # Start fresh in public schema
            connection.close()
            connection.connect()
            connection.set_schema_to_public()
            
            max_retries = 3
            retry_count = 0
            
            while retry_count < max_retries:
                try:
                    with transaction.atomic():
                        with schema_context('public'):
                            # Clean up test schools and their schemas
                            schools = School.objects.filter(schema_name__startswith='test_')
                            logger.info(f"Found {schools.count()} test schools to clean up")
                            
                            for school in schools:
                                logger.debug(f"Dropping schema {school.schema_name}")
                                with connection.cursor() as cursor: 
                                    cursor.execute(f"DROP SCHEMA IF EXISTS {school.schema_name} CASCADE")
                            schools.delete()
                            
                            # Clean up test domains
                            domains = Domain.objects.filter(domain__startswith='test.')
                            logger.debug(f"Deleting {domains.count()} test domains")
                            domains.delete()
                            
                            logger.info("Successfully cleaned up test schemas and domains")
                            break
                            
                except Exception as e:
                    logger.error(f"Error during cleanup (attempt {retry_count + 1}): {e}", exc_info=True)
                    retry_count += 1
                    if retry_count >= max_retries:
                        logger.error("Max retries reached during cleanup")
                        raise
                    
                    # Wait briefly before retrying
                    import time
                    time.sleep(0.5)
                    
                finally:
                    # Always ensure we're back in public schema with fresh connection
                    for conn in connections.all():
                        if not conn.connection.closed:
                            conn.close()
                    connection.close()
                    connection.connect()
                    connection.set_schema_to_public()
    
    request.addfinalizer(cleanup)
