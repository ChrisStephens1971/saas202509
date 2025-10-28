"""
Tenant models for multi-tenant HOA accounting system.

Each tenant represents one HOA with complete data isolation via schema-per-tenant.
"""

from django.db import models
from django.core.validators import RegexValidator
from django.utils import timezone
import uuid


class Tenant(models.Model):
    """
    Represents a single HOA (tenant) in the multi-tenant system.

    Each tenant gets its own PostgreSQL schema with isolated data.
    Schema-per-tenant provides the best security and performance for 500+ tenants.
    """

    # Status choices
    STATUS_ACTIVE = 'active'
    STATUS_INACTIVE = 'inactive'
    STATUS_SUSPENDED = 'suspended'
    STATUS_TRIAL = 'trial'

    STATUS_CHOICES = [
        (STATUS_ACTIVE, 'Active'),
        (STATUS_INACTIVE, 'Inactive'),
        (STATUS_SUSPENDED, 'Suspended'),
        (STATUS_TRIAL, 'Trial'),
    ]

    # Primary key
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="Unique identifier for this tenant"
    )

    # Tenant identification
    name = models.CharField(
        max_length=255,
        help_text="HOA name (e.g., 'Sunset Hills HOA')"
    )

    schema_name = models.CharField(
        max_length=63,  # PostgreSQL schema name limit
        unique=True,
        validators=[
            RegexValidator(
                regex=r'^[a-z][a-z0-9_]*$',
                message='Schema name must start with a letter and contain only lowercase letters, numbers, and underscores'
            )
        ],
        help_text="PostgreSQL schema name for data isolation (e.g., 'tenant_sunset_hills')"
    )

    # Contact information
    primary_contact_name = models.CharField(
        max_length=255,
        blank=True,
        help_text="Primary board contact (e.g., Board President)"
    )

    primary_contact_email = models.EmailField(
        blank=True,
        help_text="Primary contact email"
    )

    primary_contact_phone = models.CharField(
        max_length=20,
        blank=True,
        help_text="Primary contact phone"
    )

    # HOA details
    total_units = models.PositiveIntegerField(
        default=0,
        help_text="Total number of units/lots in this HOA"
    )

    address = models.TextField(
        blank=True,
        help_text="HOA mailing address"
    )

    state = models.CharField(
        max_length=2,
        blank=True,
        help_text="US state code (for state-specific lien rules)"
    )

    # Status and lifecycle
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_TRIAL,
        help_text="Current tenant status"
    )

    created_at = models.DateTimeField(
        default=timezone.now,
        editable=False,
        help_text="When this tenant was created"
    )

    activated_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When this tenant was activated (moved from trial to active)"
    )

    suspended_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When this tenant was suspended (payment issues, etc.)"
    )

    # Metadata
    settings = models.JSONField(
        default=dict,
        blank=True,
        help_text="Tenant-specific settings (timezone, date formats, etc.)"
    )

    class Meta:
        db_table = 'tenants'
        ordering = ['name']
        verbose_name = 'Tenant'
        verbose_name_plural = 'Tenants'
        indexes = [
            models.Index(fields=['schema_name']),
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.name} ({self.schema_name})"

    def activate(self):
        """Move tenant from trial to active status"""
        self.status = self.STATUS_ACTIVE
        self.activated_at = timezone.now()
        self.save(update_fields=['status', 'activated_at'])

    def suspend(self, reason=None):
        """Suspend tenant (payment issues, etc.)"""
        self.status = self.STATUS_SUSPENDED
        self.suspended_at = timezone.now()
        if reason:
            self.settings['suspension_reason'] = reason
        self.save(update_fields=['status', 'suspended_at', 'settings'])

    @property
    def is_active(self):
        """Check if tenant is active"""
        return self.status == self.STATUS_ACTIVE

    @property
    def schema_exists(self):
        """Check if PostgreSQL schema exists for this tenant"""
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT schema_name FROM information_schema.schemata WHERE schema_name = %s",
                [self.schema_name]
            )
            return cursor.fetchone() is not None
