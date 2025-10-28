"""
Custom permissions for multi-tenant HOA accounting system.

Implements role-based access control (RBAC) for API endpoints.
"""

from rest_framework import permissions
from .models import UserTenantMembership


class HasTenantAccess(permissions.BasePermission):
    """
    Permission to check if user has access to a specific tenant.
    """

    message = "You do not have access to this tenant."

    def has_permission(self, request, view):
        """Check if user has access to the tenant specified in query params"""
        if not request.user or not request.user.is_authenticated:
            return False

        # Super admin has access to all tenants
        if request.user.is_superuser:
            return True

        # Get tenant from query params or view kwargs
        tenant_id = request.query_params.get('tenant') or view.kwargs.get('tenant_id')

        if not tenant_id:
            # If no tenant specified, check if user has any tenant memberships
            return UserTenantMembership.objects.filter(
                user=request.user,
                is_active=True
            ).exists()

        # Check if user has active membership for this tenant
        return UserTenantMembership.objects.filter(
            user=request.user,
            tenant__schema_name=tenant_id,
            is_active=True
        ).exists()


class HasRolePermission(permissions.BasePermission):
    """
    Permission to check if user's role has specific permission.

    Usage:
        class MyViewSet(viewsets.ModelViewSet):
            permission_classes = [HasRolePermission]
            required_permission = 'create_invoice'
    """

    message = "Your role does not have permission to perform this action."

    def has_permission(self, request, view):
        """Check if user's role has the required permission"""
        if not request.user or not request.user.is_authenticated:
            return False

        # Super admin has all permissions
        if request.user.is_superuser:
            return True

        # Get required permission from view
        required_permission = getattr(view, 'required_permission', None)
        if not required_permission:
            # If no specific permission required, just check tenant access
            return True

        # Get tenant
        tenant_id = request.query_params.get('tenant') or view.kwargs.get('tenant_id')
        if not tenant_id:
            return False

        # Get user's membership for this tenant
        try:
            membership = UserTenantMembership.objects.get(
                user=request.user,
                tenant__schema_name=tenant_id,
                is_active=True
            )
            return membership.has_permission(required_permission)
        except UserTenantMembership.DoesNotExist:
            return False


class CanCreateInvoice(HasRolePermission):
    """Permission for creating invoices (Admin, Manager)"""

    def has_permission(self, request, view):
        view.required_permission = 'create_invoice'
        return super().has_permission(request, view)


class CanCreatePayment(HasRolePermission):
    """Permission for creating payments (Admin, Manager)"""

    def has_permission(self, request, view):
        view.required_permission = 'create_payment'
        return super().has_permission(request, view)


class CanCreateTransfer(HasRolePermission):
    """Permission for creating fund transfers (Admin, Accountant)"""

    def has_permission(self, request, view):
        view.required_permission = 'create_transfer'
        return super().has_permission(request, view)


class CanViewReports(HasRolePermission):
    """Permission for viewing reports (All roles)"""

    def has_permission(self, request, view):
        view.required_permission = 'view_reports'
        return super().has_permission(request, view)


class CanManageUsers(HasRolePermission):
    """Permission for managing users (Admin only)"""

    def has_permission(self, request, view):
        view.required_permission = 'manage_users'
        return super().has_permission(request, view)


class CanDeleteRecords(HasRolePermission):
    """Permission for deleting records (Super Admin only)"""

    def has_permission(self, request, view):
        view.required_permission = 'delete_records'
        return super().has_permission(request, view)


class IsReadOnly(permissions.BasePermission):
    """
    Permission for read-only access.
    Useful for Board Members who can only view data.
    """

    message = "Your role only has read-only access."

    def has_permission(self, request, view):
        """Allow only safe methods (GET, HEAD, OPTIONS)"""
        return request.method in permissions.SAFE_METHODS
