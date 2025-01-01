from django.conf import settings
from django.db import connection
from django_tenants.middleware import TenantMainMiddleware
from django_tenants.utils import get_tenant_domain_model
import logging

logger = logging.getLogger('apps.core')

class CustomTenantMiddleware(TenantMainMiddleware):
    """Custom middleware to handle tenant schema context properly."""
    
    def process_request(self, request):
        """Process the request and set the tenant and domain."""
        # Only reset schema if we don't already have a tenant context
        if not connection.tenant:
            connection.set_schema_to_public()
        
        # Try to get tenant from custom headers first
        tenant_id = request.META.get('HTTP_X_TENANT_ID')
        tenant_schema = request.META.get('HTTP_X_TENANT_SCHEMA')
        
        if tenant_id and tenant_schema:
            from apps.core.models import School
            try:
                tenant = School.objects.get(id=tenant_id, schema_name=tenant_schema)
                request.tenant = tenant
                connection.set_tenant(request.tenant)
                logger.debug(f"Set tenant to {request.tenant} from headers")
                return None
            except School.DoesNotExist:
                logger.warning(f"No tenant found for ID {tenant_id} and schema {tenant_schema}")
        
        # Fall back to hostname-based lookup if no tenant is set
        if not hasattr(request, 'tenant'):
            hostname = self.hostname_from_request(request)
            if hostname:
                domain_model = get_tenant_domain_model()
                try:
                    domain = domain_model.objects.select_related('tenant').get(domain=hostname)
                    request.tenant = domain.tenant
                    connection.set_tenant(request.tenant)
                    logger.debug(f"Set tenant to {request.tenant} for hostname {hostname}")
                except domain_model.DoesNotExist:
                    logger.warning(f"No tenant found for hostname {hostname}")
        
        return None
            
    def process_response(self, request, response):
        """Ensure schema is maintained throughout the response."""
        if hasattr(request, 'tenant') and request.tenant:
            connection.set_tenant(request.tenant)
            logger.debug(f"Maintaining tenant context for {request.tenant} in response")
        return response
