from django.contrib import admin
from .models import (
    Fund, AccountType, Account, JournalEntry, JournalEntryLine,
    Owner, Unit, Ownership, Invoice, InvoiceLine, Payment, PaymentApplication
)


@admin.register(AccountType)
class AccountTypeAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'normal_balance', 'description']
    readonly_fields = ['code']
    ordering = ['code']


@admin.register(Fund)
class FundAdmin(admin.ModelAdmin):
    list_display = ['name', 'fund_type', 'tenant', 'is_active', 'created_at']
    list_filter = ['fund_type', 'is_active', 'created_at']
    search_fields = ['name', 'tenant__name']
    readonly_fields = ['id', 'created_at']


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ['account_number', 'name', 'account_type', 'fund', 'tenant', 'is_active']
    list_filter = ['account_type', 'fund__fund_type', 'is_active']
    search_fields = ['account_number', 'name', 'tenant__name']
    readonly_fields = ['id', 'created_at']

    fieldsets = [
        ('Account Information', {
            'fields': ['id', 'tenant', 'fund', 'account_type', 'account_number', 'name']
        }),
        ('Details', {
            'fields': ['description', 'parent_account', 'is_active', 'created_at']
        }),
    ]


class JournalEntryLineInline(admin.TabularInline):
    model = JournalEntryLine
    extra = 2
    fields = ['line_number', 'account', 'debit_amount', 'credit_amount', 'description']
    readonly_fields = ['id']


@admin.register(JournalEntry)
class JournalEntryAdmin(admin.ModelAdmin):
    list_display = ['entry_number', 'entry_date', 'tenant', 'entry_type', 'description', 'is_balanced', 'posted_at']
    list_filter = ['entry_type', 'entry_date', 'posted_at']
    search_fields = ['entry_number', 'description', 'tenant__name']
    readonly_fields = ['id', 'entry_number', 'posted_at', 'is_balanced', 'get_totals']
    inlines = [JournalEntryLineInline]

    fieldsets = [
        ('Journal Entry Information', {
            'fields': ['id', 'tenant', 'entry_number', 'entry_date', 'entry_type']
        }),
        ('Details', {
            'fields': ['description', 'reference_id']
        }),
        ('Audit Trail', {
            'fields': ['posted_at', 'posted_by', 'reversed_by']
        }),
        ('Validation', {
            'fields': ['is_balanced', 'get_totals'],
            'classes': ['collapse']
        }),
        ('Security (Optional)', {
            'fields': ['previous_entry_hash', 'entry_hash'],
            'classes': ['collapse']
        }),
    ]

    def get_totals(self, obj):
        if obj.pk:
            debits, credits = obj.get_totals()
            return f"Debits: ${debits} | Credits: ${credits}"
        return "N/A (not saved yet)"
    get_totals.short_description = "Totals"


@admin.register(JournalEntryLine)
class JournalEntryLineAdmin(admin.ModelAdmin):
    list_display = ['journal_entry', 'line_number', 'account', 'debit_amount', 'credit_amount']
    list_filter = ['journal_entry__entry_type', 'journal_entry__entry_date']
    search_fields = ['journal_entry__entry_number', 'account__account_number', 'account__name']
    readonly_fields = ['id']


# Sprint 2: AR Models

@admin.register(Owner)
class OwnerAdmin(admin.ModelAdmin):
    list_display = ['last_name', 'first_name', 'email', 'tenant', 'status', 'is_board_member', 'created_at']
    list_filter = ['status', 'is_board_member', 'tenant', 'created_at']
    search_fields = ['first_name', 'last_name', 'email', 'tenant__name']
    readonly_fields = ['id', 'created_at', 'updated_at', 'get_ar_balance']

    fieldsets = [
        ('Owner Information', {
            'fields': ['id', 'tenant', 'first_name', 'last_name', 'email', 'phone']
        }),
        ('Address', {
            'fields': ['mailing_address']
        }),
        ('Status', {
            'fields': ['status', 'is_board_member']
        }),
        ('AR Balance', {
            'fields': ['get_ar_balance'],
            'classes': ['collapse']
        }),
        ('Notes', {
            'fields': ['notes'],
            'classes': ['collapse']
        }),
        ('Timestamps', {
            'fields': ['created_at', 'updated_at'],
            'classes': ['collapse']
        }),
    ]

    def get_ar_balance(self, obj):
        if obj.pk:
            return f"${obj.get_ar_balance():,.2f}"
        return "N/A (not saved yet)"
    get_ar_balance.short_description = "AR Balance"


@admin.register(Unit)
class UnitAdmin(admin.ModelAdmin):
    list_display = ['unit_number', 'tenant', 'monthly_assessment', 'status', 'bedrooms', 'square_feet']
    list_filter = ['status', 'tenant', 'bedrooms']
    search_fields = ['unit_number', 'property_address', 'tenant__name']
    readonly_fields = ['id', 'created_at', 'updated_at', 'get_current_owners']

    fieldsets = [
        ('Unit Information', {
            'fields': ['id', 'tenant', 'unit_number', 'property_address']
        }),
        ('Property Details', {
            'fields': ['bedrooms', 'bathrooms', 'square_feet']
        }),
        ('Financial', {
            'fields': ['monthly_assessment']
        }),
        ('Status', {
            'fields': ['status']
        }),
        ('Current Owners', {
            'fields': ['get_current_owners'],
            'classes': ['collapse']
        }),
        ('Notes', {
            'fields': ['notes'],
            'classes': ['collapse']
        }),
        ('Timestamps', {
            'fields': ['created_at', 'updated_at'],
            'classes': ['collapse']
        }),
    ]

    def get_current_owners(self, obj):
        if obj.pk:
            owners = obj.get_current_owners()
            return ", ".join([f"{o.first_name} {o.last_name}" for o in owners]) if owners else "None"
        return "N/A (not saved yet)"
    get_current_owners.short_description = "Current Owners"


@admin.register(Ownership)
class OwnershipAdmin(admin.ModelAdmin):
    list_display = ['owner', 'unit', 'ownership_percentage', 'start_date', 'end_date', 'is_current', 'tenant']
    list_filter = ['is_current', 'tenant', 'start_date']
    search_fields = ['owner__first_name', 'owner__last_name', 'unit__unit_number', 'tenant__name']
    readonly_fields = ['id', 'created_at']

    fieldsets = [
        ('Ownership Information', {
            'fields': ['id', 'tenant', 'owner', 'unit']
        }),
        ('Ownership Details', {
            'fields': ['ownership_percentage', 'start_date', 'end_date', 'is_current']
        }),
        ('Timestamps', {
            'fields': ['created_at'],
            'classes': ['collapse']
        }),
    ]


class InvoiceLineInline(admin.TabularInline):
    model = InvoiceLine
    extra = 1
    fields = ['line_number', 'description', 'account', 'amount']
    readonly_fields = ['id']


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ['invoice_number', 'owner', 'unit', 'invoice_date', 'due_date', 'total_amount', 'amount_due', 'status', 'days_overdue']
    list_filter = ['status', 'invoice_type', 'tenant', 'invoice_date', 'due_date']
    search_fields = ['invoice_number', 'owner__first_name', 'owner__last_name', 'unit__unit_number', 'tenant__name']
    readonly_fields = ['id', 'invoice_number', 'created_at', 'updated_at', 'days_overdue', 'aging_bucket']
    inlines = [InvoiceLineInline]

    fieldsets = [
        ('Invoice Information', {
            'fields': ['id', 'tenant', 'invoice_number', 'owner', 'unit']
        }),
        ('Dates', {
            'fields': ['invoice_date', 'due_date']
        }),
        ('Type and Status', {
            'fields': ['invoice_type', 'status']
        }),
        ('Amounts', {
            'fields': ['subtotal', 'late_fee', 'total_amount', 'amount_paid', 'amount_due']
        }),
        ('Description', {
            'fields': ['description']
        }),
        ('Aging', {
            'fields': ['days_overdue', 'aging_bucket'],
            'classes': ['collapse']
        }),
        ('Journal Entry Link', {
            'fields': ['journal_entry'],
            'classes': ['collapse']
        }),
        ('Timestamps', {
            'fields': ['created_at', 'updated_at'],
            'classes': ['collapse']
        }),
    ]

    def days_overdue(self, obj):
        return obj.days_overdue
    days_overdue.short_description = "Days Overdue"

    def aging_bucket(self, obj):
        return obj.aging_bucket
    aging_bucket.short_description = "Aging Bucket"


@admin.register(InvoiceLine)
class InvoiceLineAdmin(admin.ModelAdmin):
    list_display = ['invoice', 'line_number', 'description', 'account', 'amount']
    list_filter = ['invoice__tenant', 'invoice__invoice_date']
    search_fields = ['invoice__invoice_number', 'description', 'account__account_number', 'account__name']
    readonly_fields = ['id', 'created_at', 'updated_at']


class PaymentApplicationInline(admin.TabularInline):
    model = PaymentApplication
    extra = 1
    fields = ['invoice', 'amount_applied', 'notes']
    readonly_fields = ['id', 'applied_at']


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['payment_number', 'owner', 'payment_date', 'amount', 'amount_applied', 'amount_unapplied', 'payment_method', 'status']
    list_filter = ['status', 'payment_method', 'tenant', 'payment_date']
    search_fields = ['payment_number', 'owner__first_name', 'owner__last_name', 'reference_number', 'tenant__name']
    readonly_fields = ['id', 'payment_number', 'created_at', 'updated_at', 'is_fully_applied']
    inlines = [PaymentApplicationInline]

    fieldsets = [
        ('Payment Information', {
            'fields': ['id', 'tenant', 'payment_number', 'owner']
        }),
        ('Payment Details', {
            'fields': ['payment_date', 'payment_method', 'status']
        }),
        ('Amounts', {
            'fields': ['amount', 'amount_applied', 'amount_unapplied', 'is_fully_applied']
        }),
        ('Reference', {
            'fields': ['reference_number', 'notes']
        }),
        ('Journal Entry Link', {
            'fields': ['journal_entry'],
            'classes': ['collapse']
        }),
        ('Timestamps', {
            'fields': ['created_at', 'updated_at'],
            'classes': ['collapse']
        }),
    ]

    def is_fully_applied(self, obj):
        if obj.pk:
            return "Yes" if obj.is_fully_applied else "No"
        return "N/A"
    is_fully_applied.short_description = "Fully Applied"


@admin.register(PaymentApplication)
class PaymentApplicationAdmin(admin.ModelAdmin):
    list_display = ['payment', 'invoice', 'amount_applied', 'applied_at']
    list_filter = ['payment__tenant', 'applied_at']
    search_fields = ['payment__payment_number', 'invoice__invoice_number']
    readonly_fields = ['id', 'applied_at']
