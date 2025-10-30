from django.contrib import admin
from .models import (
    Fund, AccountType, Account, JournalEntry, JournalEntryLine,
    Owner, Unit, Ownership, Invoice, InvoiceLine, Payment, PaymentApplication,
    # Phase 3: Violation Tracking
    ViolationType, FineSchedule, Violation, ViolationEscalation, ViolationFine,
    # Phase 3: ARC Workflow
    ARCRequestType, ARCRequest, ARCDocument, ARCReview, ARCApproval, ARCCompletion,
    # Phase 3: Work Orders
    WorkOrderCategory, Vendor, WorkOrder, WorkOrderComment, WorkOrderAttachment, WorkOrderInvoice,
    # Phase 3: Reserve Planning (already existed)
    ReserveStudy, ReserveComponent, ReserveScenario,
    # Phase 3: Budget (already existed)
    Budget, BudgetLine
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


# ============================================================================
# PHASE 3: OPERATIONAL FEATURES - Admin Registrations
# ============================================================================

# ----------------------------------------------------------------------------
# Sprint 15: Violation Tracking
# ----------------------------------------------------------------------------

@admin.register(ViolationType)
class ViolationTypeAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'category', 'tenant', 'is_active']
    list_filter = ['category', 'is_active', 'tenant']
    search_fields = ['code', 'name', 'category']
    readonly_fields = ['id', 'created_at', 'updated_at']


@admin.register(FineSchedule)
class FineScheduleAdmin(admin.ModelAdmin):
    list_display = ['violation_type', 'step_number', 'step_name', 'fine_amount', 'days_after_previous']
    list_filter = ['violation_type', 'requires_board_approval']
    search_fields = ['violation_type__code', 'step_name']
    readonly_fields = ['id', 'created_at']


@admin.register(Violation)
class ViolationAdmin(admin.ModelAdmin):
    list_display = ['unit', 'owner', 'violation_type', 'status', 'discovered_date', 'cured_date', 'tenant']
    list_filter = ['status', 'tenant', 'discovered_date']
    search_fields = ['unit__unit_number', 'owner__last_name', 'description']
    readonly_fields = ['id', 'created_at', 'updated_at']


@admin.register(ViolationEscalation)
class ViolationEscalationAdmin(admin.ModelAdmin):
    list_display = ['violation', 'step_number', 'step_name', 'fine_amount', 'escalated_at', 'notice_sent']
    list_filter = ['step_name', 'notice_sent', 'escalated_at']
    search_fields = ['violation__id', 'tracking_number']
    readonly_fields = ['id', 'escalated_at']


@admin.register(ViolationFine)
class ViolationFineAdmin(admin.ModelAdmin):
    list_display = ['violation', 'amount', 'status', 'posted_date', 'paid_date']
    list_filter = ['status', 'posted_date']
    search_fields = ['violation__id', 'invoice__invoice_number']
    readonly_fields = ['id', 'created_at', 'updated_at']


# ----------------------------------------------------------------------------
# Sprint 16: ARC Workflow
# ----------------------------------------------------------------------------

@admin.register(ARCRequestType)
class ARCRequestTypeAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'requires_plans', 'requires_contractor', 'typical_review_days', 'is_active']
    list_filter = ['requires_plans', 'requires_contractor', 'is_active']
    search_fields = ['code', 'name']
    readonly_fields = ['id', 'created_at', 'updated_at']


@admin.register(ARCRequest)
class ARCRequestAdmin(admin.ModelAdmin):
    list_display = ['title', 'unit', 'owner', 'request_type', 'status', 'submitted_at', 'tenant']
    list_filter = ['status', 'request_type', 'tenant', 'submitted_at']
    search_fields = ['title', 'unit__unit_number', 'owner__last_name', 'description']
    readonly_fields = ['id', 'created_at', 'updated_at']


@admin.register(ARCDocument)
class ARCDocumentAdmin(admin.ModelAdmin):
    list_display = ['request', 'document_type', 'file_name', 'file_size', 'uploaded_at']
    list_filter = ['document_type', 'uploaded_at']
    search_fields = ['request__title', 'file_name']
    readonly_fields = ['id', 'uploaded_at']


@admin.register(ARCReview)
class ARCReviewAdmin(admin.ModelAdmin):
    list_display = ['request', 'reviewer', 'decision', 'review_date']
    list_filter = ['decision', 'review_date']
    search_fields = ['request__title', 'reviewer__username', 'comments']
    readonly_fields = ['id', 'review_date']


@admin.register(ARCApproval)
class ARCApprovalAdmin(admin.ModelAdmin):
    list_display = ['request', 'final_decision', 'decision_date', 'approved_by', 'expiration_date']
    list_filter = ['final_decision', 'decision_date']
    search_fields = ['request__title', 'board_resolution']
    readonly_fields = ['id', 'created_at']


@admin.register(ARCCompletion)
class ARCCompletionAdmin(admin.ModelAdmin):
    list_display = ['request', 'inspection_date', 'complies_with_approval', 'inspected_by']
    list_filter = ['complies_with_approval', 'inspection_date']
    search_fields = ['request__title', 'inspector_notes']
    readonly_fields = ['id', 'created_at']


# ----------------------------------------------------------------------------
# Sprint 17: Work Order System
# ----------------------------------------------------------------------------

@admin.register(WorkOrderCategory)
class WorkOrderCategoryAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'default_gl_account', 'tenant', 'is_active']
    list_filter = ['is_active', 'tenant']
    search_fields = ['code', 'name']
    readonly_fields = ['id', 'created_at', 'updated_at']


@admin.register(Vendor)
class VendorAdmin(admin.ModelAdmin):
    list_display = ['name', 'contact_name', 'phone', 'email', 'specialty', 'is_active', 'tenant']
    list_filter = ['specialty', 'is_active', 'tenant']
    search_fields = ['name', 'contact_name', 'email', 'license_number']
    readonly_fields = ['id', 'created_at', 'updated_at']


@admin.register(WorkOrder)
class WorkOrderAdmin(admin.ModelAdmin):
    list_display = ['work_order_number', 'title', 'category', 'priority', 'status', 'assigned_to_vendor', 'requested_date']
    list_filter = ['priority', 'status', 'category', 'tenant', 'requested_date']
    search_fields = ['work_order_number', 'title', 'description', 'location']
    readonly_fields = ['id', 'created_at', 'updated_at']


@admin.register(WorkOrderComment)
class WorkOrderCommentAdmin(admin.ModelAdmin):
    list_display = ['work_order', 'commented_by', 'commented_at', 'is_internal']
    list_filter = ['is_internal', 'commented_at']
    search_fields = ['work_order__work_order_number', 'comment']
    readonly_fields = ['id', 'commented_at']


@admin.register(WorkOrderAttachment)
class WorkOrderAttachmentAdmin(admin.ModelAdmin):
    list_display = ['work_order', 'file_name', 'uploaded_by', 'uploaded_at']
    list_filter = ['uploaded_at']
    search_fields = ['work_order__work_order_number', 'file_name']
    readonly_fields = ['id', 'uploaded_at']


@admin.register(WorkOrderInvoice)
class WorkOrderInvoiceAdmin(admin.ModelAdmin):
    list_display = ['work_order', 'vendor', 'invoice_number', 'invoice_date', 'amount', 'payment_status']
    list_filter = ['payment_status', 'vendor', 'invoice_date']
    search_fields = ['invoice_number', 'work_order__work_order_number', 'vendor__name']
    readonly_fields = ['id', 'created_at', 'updated_at']


# ----------------------------------------------------------------------------
# Sprint 14: Reserve Planning (models already existed)
# ----------------------------------------------------------------------------

@admin.register(ReserveStudy)
class ReserveStudyAdmin(admin.ModelAdmin):
    list_display = ['name', 'study_date', 'horizon_years', 'current_reserve_balance', 'tenant']
    list_filter = ['study_date', 'tenant']
    search_fields = ['name', 'notes']
    readonly_fields = ['id', 'created_at', 'updated_at']


@admin.register(ReserveComponent)
class ReserveComponentAdmin(admin.ModelAdmin):
    list_display = ['name', 'study', 'useful_life_years', 'remaining_life_years', 'replacement_cost', 'category']
    list_filter = ['category', 'study']
    search_fields = ['name', 'description']
    readonly_fields = ['id', 'inflation_adjusted_cost', 'created_at', 'updated_at']


@admin.register(ReserveScenario)
class ReserveScenarioAdmin(admin.ModelAdmin):
    list_display = ['name', 'study', 'monthly_contribution', 'one_time_contribution']
    list_filter = ['study']
    search_fields = ['name', 'notes']
    readonly_fields = ['id', 'created_at', 'updated_at']


# ----------------------------------------------------------------------------
# Sprint 18: Budget Tracking (models already existed)
# ----------------------------------------------------------------------------

@admin.register(Budget)
class BudgetAdmin(admin.ModelAdmin):
    list_display = ['fiscal_year', 'tenant', 'start_date', 'end_date', 'status']
    list_filter = ['fiscal_year', 'status', 'tenant']
    search_fields = ['notes']
    readonly_fields = ['id', 'created_at', 'updated_at']


@admin.register(BudgetLine)
class BudgetLineAdmin(admin.ModelAdmin):
    list_display = ['budget', 'fund', 'gl_account', 'category', 'annual_amount', 'monthly_amount']
    list_filter = ['category', 'fund', 'budget']
    search_fields = ['gl_account__account_number', 'gl_account__name', 'notes']
    readonly_fields = ['id']
