"""
Middleware for HOA accounting system.

Provides audit logging and tenant context management.
"""

import json
from django.utils.deprecation import MiddlewareMixin
from .models import AuditLog


class AuditLoggingMiddleware(MiddlewareMixin):
    """
    Middleware to log all important API requests for audit purposes.

    Logs:
    - All POST, PUT, PATCH, DELETE requests
    - User authentication
    - Tenant context
    """

    def process_request(self, request):
        """Store request data for later logging"""
        # Store original request data for comparison in process_response
        if request.method in ['POST', 'PUT', 'PATCH', 'DELETE']:
            try:
                request._audit_data = {
                    'method': request.method,
                    'path': request.path,
                    'user': request.user if hasattr(request, 'user') else None,
                    'body': request.body.decode('utf-8') if request.body else None,
                }
            except Exception:
                pass  # Don't break request if audit logging fails

    def process_response(self, request, response):
        """Log the request after it completes"""
        # Only log if we have audit data and user is authenticated
        if not hasattr(request, '_audit_data'):
            return response

        audit_data = request._audit_data

        # Only log authenticated requests
        if not audit_data['user'] or not audit_data['user'].is_authenticated:
            return response

        # Determine action type
        action = self._get_action_from_method(audit_data['method'])

        # Get tenant from query params or URL
        tenant_id = request.GET.get('tenant')
        if not tenant_id and hasattr(request, 'resolver_match'):
            tenant_id = request.resolver_match.kwargs.get('tenant_id')

        # Only log if we have a tenant
        if not tenant_id:
            return response

        # Try to get tenant object
        try:
            from tenants.models import Tenant
            tenant = Tenant.objects.get(schema_name=tenant_id)
        except Tenant.DoesNotExist:
            return response

        # Determine model name from path
        model_name = self._get_model_from_path(request.path)

        # Parse request body for changes
        changes = {}
        if audit_data['body']:
            try:
                changes = json.loads(audit_data['body'])
            except json.JSONDecodeError:
                pass

        # Create audit log (don't fail request if this fails)
        try:
            AuditLog.log(
                tenant=tenant,
                user=audit_data['user'],
                action=action,
                model_name=model_name,
                changes=changes,
                request=request
            )
        except Exception:
            pass  # Don't break the request if audit logging fails

        return response

    def _get_action_from_method(self, method):
        """Map HTTP method to audit action"""
        mapping = {
            'POST': AuditLog.ACTION_CREATE,
            'PUT': AuditLog.ACTION_UPDATE,
            'PATCH': AuditLog.ACTION_UPDATE,
            'DELETE': AuditLog.ACTION_DELETE,
        }
        return mapping.get(method, AuditLog.ACTION_UPDATE)

    def _get_model_from_path(self, path):
        """Extract model name from URL path"""
        # Example: /api/v1/accounting/invoices/ -> Invoice
        parts = path.strip('/').split('/')
        if len(parts) >= 4 and parts[2] == 'accounting':
            model_name = parts[3].rstrip('s').title()
            return model_name
        return 'Unknown'


class TenantContextMiddleware(MiddlewareMixin):
    """
    Middleware to add tenant context to requests.

    Attaches the tenant object to the request for easy access in views.
    """

    def process_request(self, request):
        """Add tenant to request object"""
        tenant_id = request.GET.get('tenant')

        if not tenant_id and hasattr(request, 'resolver_match') and request.resolver_match:
            tenant_id = request.resolver_match.kwargs.get('tenant_id')

        if tenant_id:
            try:
                from tenants.models import Tenant
                request.tenant = Tenant.objects.get(schema_name=tenant_id)
            except Tenant.DoesNotExist:
                request.tenant = None
        else:
            request.tenant = None

        return None
