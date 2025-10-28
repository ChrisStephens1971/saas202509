from django.contrib import admin
from .models import Tenant


@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display = ['name', 'schema_name', 'status', 'total_units', 'state', 'created_at']
    list_filter = ['status', 'state', 'created_at']
    search_fields = ['name', 'schema_name', 'primary_contact_name', 'primary_contact_email']
    readonly_fields = ['id', 'created_at', 'schema_exists']

    fieldsets = [
        ('Tenant Information', {
            'fields': ['id', 'name', 'schema_name', 'status']
        }),
        ('Contact Details', {
            'fields': ['primary_contact_name', 'primary_contact_email', 'primary_contact_phone']
        }),
        ('HOA Details', {
            'fields': ['total_units', 'address', 'state']
        }),
        ('Lifecycle', {
            'fields': ['created_at', 'activated_at', 'suspended_at']
        }),
        ('Settings', {
            'fields': ['settings'],
            'classes': ['collapse']
        }),
    ]
